from django.db import models


class BaseManager(models.Manager):

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_delete=0)
        return queryset


class BaseField(models.Model):

    createtime = models.DateTimeField('创建时间', auto_now_add=True)
    modifytime = models.DateTimeField('修改时间', auto_now=True)
    remark = models.CharField('备注',
                              max_length=32,
                              null=True,
                              default=None,
                              blank=True)
    is_delete = models.IntegerField(default=0)
    objects = BaseManager()

    class Meta:
        abstract = True
