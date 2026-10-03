import csv
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from django.views import View
from django.db.models import Q

from .models import Opportunity, Comment
from .forms import AddOpportunityForm, AddCommentForm


class OpportunityListView(LoginRequiredMixin, ListView):
    model = Opportunity
    template_name = 'opportunity/opportunity_list.html'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(created_by=self.request.user)

        query = self.request.GET.get('q')
        if query:
            # Match every term separately, so "acme smith" finds the opportunity
            # whose account is "Smith John - Acme" regardless of the word order.
            for term in re.split(r'[\s,\-/]+', query):
                if not term:
                    continue
                queryset = queryset.filter(
                    Q(name__icontains=term) |
                    Q(account__company__icontains=term) |
                    Q(account__first_name__icontains=term) |
                    Q(account__last_name__icontains=term)
                )

        stage = self.request.GET.get('stage')
        if stage:
            queryset = queryset.filter(stage=stage)

        sort = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort)

        return queryset


class OpportunityDetailView(LoginRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'opportunity/opportunity_detail.html'

    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user, pk=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AddCommentForm()

        comment_list = Comment.objects.filter(opportunity_id=self.kwargs.get('pk')).order_by('-created_at')
        comment_paginator = Paginator(comment_list, 5)
        comment_page_number = self.request.GET.get('comment_page')
        context['comments'] = comment_paginator.get_page(comment_page_number)

        return context


class OpportunityCreateView(LoginRequiredMixin, CreateView):
    model = Opportunity
    form_class = AddOpportunityForm
    template_name = 'opportunity/opportunity_form.html'
    success_url = reverse_lazy('opportunity:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Opportunity'
        return context

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error)
        return super().form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return redirect(self.get_success_url())


class OpportunityUpdateView(LoginRequiredMixin, UpdateView):
    model = Opportunity
    form_class = AddOpportunityForm
    template_name = 'opportunity/opportunity_form.html'
    success_url = reverse_lazy('opportunity:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Opportunity'
        return context

    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user, pk=self.kwargs.get('pk'))


class OpportunityDeleteView(LoginRequiredMixin, DeleteView):
    model = Opportunity
    success_url = reverse_lazy('opportunity:list')

    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user, pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        form = AddCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.created_by = request.user
            comment.opportunity_id = pk
            comment.save()
            messages.success(request, "Comment added successfully.")
        else:
            messages.error(request, "Failed to add comment. Please try again.")
        return redirect('opportunity:detail', pk=pk)


class EditCommentView(LoginRequiredMixin, View):
    def post(self, request, opportunity_id, comment_id):
        opportunity = get_object_or_404(Opportunity, id=opportunity_id)
        comment = get_object_or_404(Comment, id=comment_id, opportunity=opportunity)

        if request.user != comment.created_by and not request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to edit this comment.")

        content = request.POST.get("content")
        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Comment updated successfully.")
        else:
            messages.error(request, "Content cannot be empty.")

        return redirect('opportunity:detail', pk=opportunity_id)


@login_required
def delete_comment(request, opportunity_id, comment_id):
    opportunity = get_object_or_404(Opportunity, id=opportunity_id)
    comment = get_object_or_404(Comment, id=comment_id, opportunity=opportunity)

    if request.user == comment.created_by or request.user.is_staff:
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this comment.")

    return redirect('opportunity:detail', pk=opportunity.id)


@login_required
def opportunity_export(request):
    opportunities = Opportunity.objects.filter(created_by=request.user)

    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="opportunities.csv"'}
                            )

    writer = csv.writer(response)
    writer.writerow(['Name', 'Account', 'Stage', 'Probability', 'Amount', 'Currency', 'Close date'])

    for opportunity in opportunities:
        # expected_close_date is nullable, so guard before formatting it
        close_date = opportunity.expected_close_date
        writer.writerow([opportunity.name, opportunity.account or '', opportunity.get_stage_display(),
                         opportunity.probability, opportunity.amount, opportunity.currency,
                         close_date.strftime('%d-%m-%Y') if close_date else ''])
    return response


@login_required
def opportunities_bulk_delete(request):
    if request.method == "POST":
        opportunity_ids = request.POST.getlist('opportunity_ids')
        selected_opportunities = request.POST.getlist('opportunity_ids')

        if opportunity_ids:
            Opportunity.objects.filter(id__in=opportunity_ids, created_by=request.user).delete()

            messages.success(request, f"Selected opportunities were deleted successfully.")
        elif selected_opportunities:
            Opportunity.objects.filter(id__in=selected_opportunities, created_by=request.user).delete()
            messages.success(request, f"Selected opportunities were deleted successfully.")
        else:
            messages.warning(request, f"No opportunities were selected for deletion.")
    return redirect('opportunity:list')
