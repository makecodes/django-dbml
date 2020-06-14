# django-dbml

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
$ python manage.py dbml all
```
