# -*- coding: utf-8 -*-
import io
import gzip
import json

from six import text_type

from twisted.internet import defer


def gzipdata(data):
    if isinstance(data, text_type):
        data = data.encode()

    fgz = io.BytesIO()
    gzip_obj = gzip.GzipFile(mode='wb', fileobj=fgz)
    gzip_obj.write(data)
    gzip_obj.close()

    return fgz.getvalue()


class ApiCache(object):
    memory_cache_dict = {}

    @classmethod
    def get(cls, tid, resource, language):
        if tid in cls.memory_cache_dict \
           and resource in cls.memory_cache_dict[tid] \
           and language in cls.memory_cache_dict[tid][resource]:
            return cls.memory_cache_dict[tid][resource][language]

    @classmethod
    def set(cls, tid, resource, language, content_type, data):
        data = gzipdata(data)

        if tid not in ApiCache.memory_cache_dict:
            cls.memory_cache_dict[tid] = {}

        if resource not in ApiCache.memory_cache_dict[tid]:
            cls.memory_cache_dict[tid][resource] = {}

        entry = (content_type, data)

        cls.memory_cache_dict[tid][resource][language] = entry

        return entry

    @classmethod
    def invalidate(cls, tid=None):
        if tid is not None:
            cls.memory_cache_dict.pop(tid, None)
        else:
            cls.memory_cache_dict.clear()


def decorator_cache_get(f):
    def decorator_cache_get_wrapper(self, *args, **kwargs):
        c = ApiCache.get(self.request.tid, self.request.path, self.request.language)
        if c is None:
            d = defer.maybeDeferred(f, self, *args, **kwargs)

            def callback(data):
                if isinstance(data, (dict, list)):
                    self.request.setHeader(b'content-type', b'application/json')
                    data = json.dumps(data)

                self.request.setHeader(b'Content-encoding', b'gzip')

                c = self.request.responseHeaders.getRawHeaders(b'Content-type', [b'application/json'])[0]
                return ApiCache.set(self.request.tid, self.request.path, self.request.language, c, data)[1]

            d.addCallback(callback)

            return d

        else:
            self.request.setHeader(b'Content-encoding', b'gzip')
            self.request.setHeader(b'Content-type', c[0])

        return c[1]

    return decorator_cache_get_wrapper


def decorator_cache_invalidate(f):
    def decorator_cache_invalidate_wrapper(self, *args, **kwargs):
        if self.invalidate_cache and self.request.tid != 1:
            ApiCache.invalidate(self.request.tid)
        else:
            ApiCache.invalidate()

        return f(self, *args, **kwargs)

    return decorator_cache_invalidate_wrapper
