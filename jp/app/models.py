from django.db import models
from django.contrib.auth.models import User


class Section(models.Model):
    name = models.CharField(max_length=100)

class Type(models.Model):
    name = models.CharField(max_length=100)

class Employee(models.Model):
    fullname = models.CharField(max_length=100)
    image = models.ImageField(upload_to='image/',null=True)
    date = models.DateField(null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    address = models.TextField(null=True)
    phonenumber = models.CharField(max_length=10,null=True)
    pincode = models.CharField(max_length=10,null=True)
    state = models.CharField(max_length=100,null=True)
    city = models.CharField(max_length=100,null=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    resume = models.FileField(upload_to='image/',null=True, blank=True)


class Education(models.Model):
    course = models.CharField(max_length=100)
    institute = models.CharField(max_length=100)
    fromd = models.DateField()
    tod = models.DateField()
    document = models.FileField(upload_to='image/',null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)

class Experiance(models.Model):
    position = models.CharField(max_length=100)
    institute = models.CharField(max_length=100)
    description = models.TextField()
    fromd = models.DateField()
    tod = models.DateField()
    document = models.FileField(upload_to='image/',null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)

class Skills(models.Model):
    name = models.CharField(max_length=100)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)

class Employer(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='image/',null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    address = models.TextField(null=True)
    phonenumber = models.CharField(max_length=10,null=True)
    pincode = models.CharField(max_length=10,null=True)
    state = models.CharField(max_length=100,null=True)
    city = models.CharField(max_length=100,null=True)
    status = models.BinaryField(default=False)
    description = models.TextField(null=True)
    document = models.FileField(upload_to='image/',null=True, blank=True)
    



class Job(models.Model):
    PENDING = 'P'
    APPROVED = 'A'
    REJECTED = 'R'
    NONE = 'N'  # Represents the None state

    APPROVAL_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (NONE, 'None'),
    ]

    status = models.CharField(
        max_length=1,
        choices=APPROVAL_CHOICES,
        default=NONE,  # Default to None state
    )
    approval = models.BooleanField(null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True)
    type = models.ForeignKey(Type, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=100)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, null=True, blank=True)
    experiance = models.CharField(max_length=100, null=True)
    skills = models.TextField(null=True)
    noti = models.BinaryField(default=False)
    city = models.CharField(max_length=100,null=True)
    fromd = models.DateField(null=True)
    tod = models.DateField(null=True)
    education = models.CharField(max_length=100,null=True)
    description = models.TextField(null=True)
    is_saved = models.BinaryField(default=False)
    


