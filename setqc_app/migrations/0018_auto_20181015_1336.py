# Generated by Django 2.0.6 on 2018-10-15 20:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setqc_app', '0017_librariessetqc_genomeinfo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='librariessetqc',
            old_name='genomeinfo',
            new_name='genome',
        ),
    ]