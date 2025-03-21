# Generated by Django 5.0.4 on 2025-03-06 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Teacher', '0004_shell_video_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='shell',
            name='pdf_file',
            field=models.FileField(blank=True, null=True, upload_to='shell_pdfs/'),
        ),
        migrations.AddField(
            model_name='shell',
            name='video_file',
            field=models.FileField(blank=True, null=True, upload_to='shell_videos/'),
        ),
    ]
