from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import IDeserializeFromJson
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from collective.easyform.interfaces import IEasyForm
from plone.restapi.serializer.dxcontent import SerializeToJson as DXContentToJson
from plone.restapi.deserializer.dxcontent import (
    DeserializeFromJson as DXContentFromJson,
)
from plone.restapi.deserializer import json_body
from zope.schema import getFieldsInOrder
from collective.easyform.api import get_actions
from collective.easyform.interfaces import ISaveData


@implementer(ISerializeToJson)
@adapter(IEasyForm, Interface)
class SerializeToJson(DXContentToJson):
    def __call__(self, version=None, include_items=True):
        result = super(SerializeToJson, self).__call__(version, include_items)
        self.serializeSavedData(result)

        return result

    def serializeSavedData(self, result):
        storage = dict()
        actions = getFieldsInOrder(get_actions(self.context))
        for name, action in actions:
            if ISaveData.providedBy(action):
                serializeable = dict()
                storage[name] = serializeable
                for key, value in action.getSavedFormInputItems():
                    serializeable[key] = value
        if storage:
            result["savedDataStorage"] = storage


@implementer(IDeserializeFromJson)
@adapter(IEasyForm, Interface)
class DeserializeFromJson(DXContentFromJson):
    def __call__(
        self, validate_all=False, data=None, create=False, mask_validation_errors=True
    ):  # noqa: ignore=C901

        if data is None:
            data = json_body(self.request)

        super(DeserializeFromJson, self).__call__(
            validate_all, data, create, mask_validation_errors
        )

        self.deserializeSavedData(data)

    def deserializeSavedData(self, data):
        if hasattr(data, "savedDataStorage"):
            actions = getFieldsInOrder(get_actions(self.context))
            for name, action in actions:
                if ISaveData.providedBy(action):
                    savedData = data.savedDataStorage[name]
                    for key, value in savedData.items():
                        action.setDataRow(key, value)
