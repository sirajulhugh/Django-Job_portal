from django.test import TestCase

# Create your tests here.
@user_passes_test(admin_check, login_url='login') 
  
@user_passes_test(staff_check, login_url='login') 

@user_passes_test(regular_user_check, login_url='login') 