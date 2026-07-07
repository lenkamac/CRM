from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
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
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(account__company__icontains=query) |
                Q(campaign__icontains=query)
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
