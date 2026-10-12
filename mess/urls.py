from django.urls import path
from . import views

urlpatterns = [
    path("", views.MenuView.as_view(), name="mess_menu"),
    path("menu/edit/", views.MenuEditView.as_view(), name="menu_edit"),
    path("my/", views.MyMealsView.as_view(), name="my_meals"),
    path("toggle/", views.ToggleMealView.as_view(), name="toggle_meal"),
    path("count/", views.MealCountView.as_view(), name="meal_count"),
    path("feedback/new/", views.FeedbackCreateView.as_view(), name="feedback_add"),
    path("feedback/", views.FeedbackListView.as_view(), name="feedback_list"),
]