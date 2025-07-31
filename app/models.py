from datetime import datetime, timezone
from hashlib import md5
from hmac import digest
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

from app import db

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True))


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(240))

    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    posts: so.WriteOnlyMapped['Post'] = so.relationship(
        back_populates='author')

    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers,
        primaryjoin=(id == followers.c.follower_id),
        secondaryjoin=(id == followers.c.followed_id),
        back_populates='followers')

    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers,
        primaryjoin=(id == followers.c.followed_id),
        secondaryjoin=(id == followers.c.follower_id),
        back_populates='following'
    )

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user: 'User') -> None:
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user: 'User') -> bool:
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)


    def following_posts(self):
        Author = so.aliased(User)    # User này là tác giả của bài post
        Follower = so.aliased(User)  # User này là người đang follow

        return (
            sa.select(Post) # Chọn tất cả các bài post
            .join(Post.author.of_type(Author)) # Kết nối bài post với tác giả của nó (mà ta gọi là Author)
            .join(Author.followers.of_type(Follower)) # Từ tác giả, kết nối đến những người follow tác giả (mà ta gọi là Follower)
            .where(Follower.id == self.id) # Chỉ lấy những bài post mà tác giả của chúng được follow bởi user hiện tại (self.id)
            .order_by(Post.timestamp.desc()) # Sắp xếp bài post theo thời gian giảm dần (mới nhất trước)
        )



class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)

    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
