from django.db import models
from django.contrib.auth import get_user_model


class Category(models.Model):
    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField('Идентификатор', unique=True,
                            help_text=('Идентификатор страницы для URL; '
                                       'разрешены символы латиницы, цифры, '
                                       'дефис и подчёркивание.'))
    is_published = models.BooleanField(
        'Опубликовано', default=True, help_text=('Снимите галочку, '
                                                 'чтобы скрыть публикацию.'))
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        
    def __str__(self):
        return self.title


class Location(models.Model):
    name = models.CharField('Название места', max_length=256)
    is_published = models.BooleanField(
        'Опубликовано', default=True,
        help_text=('Снимите '
                   'галочку, чтобы скрыть публикацию.'))
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
    
    def __str__(self):
        return self.name


User = get_user_model()


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=('Если установить дату и время в '
                   'будущем — можно делать отложенные публикации.'))
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор публикации')
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True,
        verbose_name='Местоположение')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True,
        verbose_name='Категория')
    is_published = models.BooleanField(
        'Опубликовано', default=True,
        help_text=('Снимите'
                   ' галочку, чтобы скрыть публикацию.'))
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    image = models.ImageField('Фото', upload_to='photo_post', blank=True)

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return self.title


class Comments(models.Model):
    text = models.TextField('Текст комментария')
    post_info = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    created_time = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('created_time',)

    @property
    def post_id(self):
        return self.post_info.id