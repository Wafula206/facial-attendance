from django.db import models
from django.conf import settings
import pickle
import json


class FaceEmbedding(models.Model):
    """
    Store face embeddings in database
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='face_embeddings'
    )
    
    embedding_binary = models.BinaryField(null=True, blank=True)
    embedding_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'recognition_face_embeddings'
    
    def save_embedding(self, embedding_list):
        if isinstance(embedding_list, list):
            self.embedding_binary = pickle.dumps(embedding_list)
            self.embedding_json = embedding_list
    
    def get_embedding(self):
        if self.embedding_binary:
            try:
                return pickle.loads(self.embedding_binary)
            except:
                pass
        return self.embedding_json
    
    def __str__(self):
        return f"FaceEmbedding for {self.user.username}"
