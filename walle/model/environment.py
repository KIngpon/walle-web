# -*- coding: utf-8 -*-
"""
    walle-web

    :copyright: © 2015-2019 walle-web.io
    :created time: 2018-11-24 07:18:16
    :author: wushuiyong@walle-web.io
"""
from datetime import datetime

from sqlalchemy import String, Integer, DateTime
from walle.model.database import db, Model
from walle.service.extensions import permission
from walle.service.rbac.role import *
from walle import model


# 环境级别
class EnvironmentModel(Model):
    # 表的名字:
    __tablename__ = 'environments'
    __table_args__ = {"useexisting": True}
    status_open = 1
    status_close = 2
    current_time = datetime.now()

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(20))
    space_id = db.Column(Integer)
    status = db.Column(Integer)
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    def list(self, page=0, size=10, kw=None, space_id=None):
        """
        获取分页列表
        :param page:
        :param size:
        :param kw:
        :return:
        """
        query = self.query.filter(EnvironmentModel.status.notin_([self.status_remove]))
        if kw:
            query = query.filter(EnvironmentModel.name.like('%' + kw + '%'))
        if space_id:
            query = query.filter(EnvironmentModel.space_id==space_id)

        SpaceModel = model.space.SpaceModel
        query = query.join(SpaceModel, SpaceModel.id==EnvironmentModel.space_id)
        query = query.add_columns(SpaceModel.name)
        count = query.count()
        data = query.order_by(EnvironmentModel.id.desc()).offset(int(size) * int(page)).limit(size).all()

        current_app.logger.info(data)
        env_list = []
        for p in data:
            item = p[0].to_json()
            item['space_name'] = p[1]
            env_list.append(item)

        return env_list, count

    def item(self, env_id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        data = self.query.filter(EnvironmentModel.status.notin_([self.status_remove])).filter_by(id=self.id).first()
        return data.to_json() if data else []

    def add(self, env_name, space_id):
        # todo permission_ids need to be formated and checked
        env = EnvironmentModel(name=env_name, status=self.status_open, space_id=space_id)

        db.session.add(env)
        db.session.commit()

        if env.id:
            self.id = env.id

        return env.id

    def update(self, env_name, status, env_id=None):
        # todo permission_ids need to be formated and checked
        role = EnvironmentModel.query.filter_by(id=self.id).first()
        role.name = env_name
        role.status = status
        ret = db.session.commit()

        return ret

    def remove(self, env_id=None):
        """

        :param role_id:
        :return:
        """
        self.query.filter_by(id=self.id).update({'status': self.status_remove})
        ret = db.session.commit()

        return ret

    def to_json(self):
        item = {
            'id': self.id,
            'status': self.status,
            'space_id': self.space_id,
            'env_name': self.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        item.update(self.enable())
        return item

    def enable(self):
        return {
            'enable_update': permission.enable_role(DEVELOPER),
            'enable_delete': permission.enable_role(DEVELOPER),
            'enable_create': False,
            'enable_online': False,
            'enable_audit': False,
            'enable_block': False,
        }
