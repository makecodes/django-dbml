# Django DBML generator

This app can generate a DBML output for all installed models.

## How to install and use?

#### 1. Install the django-dbml package

```
pip install django-dbml
```

#### 2. Put django_dbml on your django settings

```python
'...',
'django_dbml',
'...',
```

#### 3. Run the command to generate a DBML schema based on your Django models

```bash
$ python manage.py dbml
```

To generate DBML for a subset of your models, specify one or more Django app 
names or models by app_label or app_label.ModelName. Related tables will still 
be included in the DBML.

# Thanks

The initial code was based on https://github.com/hamedsj/DbmlForDjango project
