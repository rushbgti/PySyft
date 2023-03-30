# Reference: https://github.com/pydantic/pydantic/issues/1223#issuecomment-998160737


# stdlib
import inspect
import threading
from typing import Any
from typing import Dict
from typing import T
from typing import Tuple
from typing import Type
from typing import Union

# third party
from pydantic.fields import UndefinedType
from pydantic.main import BaseModel
from pydantic.main import ModelField
from pydantic.main import ModelMetaclass


class Empty:
    pass


EmptyType = Union[T, Empty]


class PartialModelMetaclass(ModelMetaclass):
    def __new__(
        meta: Type["PartialModelMetaclass"], *args: Any, **kwargs: Any
    ) -> "PartialModelMetaclass":
        cls = super(PartialModelMetaclass, meta).__new__(meta, *args, *kwargs)
        cls_init = cls.__init__
        # Because the class will be modified temporarily, need to lock __init__
        init_lock = threading.Lock()
        # To preserve identical hashes of temporary nested partial models,
        # only one instance of each temporary partial class can exist
        temporary_partial_classes: Dict[str, ModelMetaclass] = {}

        def __init__(self: BaseModel, *args: Any, **kwargs: Any) -> None:
            with init_lock:
                fields = self.__class__.__fields__
                fields_map: Dict[ModelField, Tuple[Any, bool]] = {}

                def optionalize(
                    fields: Dict[str, ModelField], *, restore: bool = False
                ) -> None:
                    for _, field in fields.items():
                        if not restore:
                            assert not isinstance(field.required, UndefinedType)
                            fields_map[field] = (field.type_, field.required)
                            # If field has None allowed as a value
                            # then it becomes a required field.
                            if field.allow_none and field.name in kwargs:
                                field.required = True
                            else:
                                field.required = False
                            if (
                                inspect.isclass(field.type_)
                                and issubclass(field.type_, BaseModel)
                                and not field.type_.__name__.startswith(
                                    "TemporaryPartial"
                                )
                            ):
                                # Assign a temporary type to optionalize to avoid
                                # modifying *other* classes
                                class_name = f"TemporaryPartial{field.type_.__name__}"
                                if class_name in temporary_partial_classes:
                                    field.type_ = temporary_partial_classes[class_name]
                                else:
                                    field.type_ = ModelMetaclass(
                                        class_name,
                                        (field.type_,),
                                        {},
                                    )
                                    temporary_partial_classes[class_name] = field.type_

                                field.populate_validators()
                                if field.sub_fields is not None:
                                    for sub_field in field.sub_fields:
                                        sub_field.type_ = field.type_
                                        sub_field.populate_validators()
                                optionalize(field.type_.__fields__)
                        else:
                            # No need to recursively de-optionalize once original types
                            # are restored
                            field.type_, field.required = fields_map[field]
                            if field.sub_fields is not None:
                                for sub_field in field.sub_fields:
                                    sub_field.type_ = field.type_

                # Make fields and fields of nested model types optional
                optionalize(fields)
                # Transform kwargs that are PartialModels to their dict() forms. This
                # will exclude `None` (see below) from the dictionary used to construct
                # the temporarily-partial model field, avoiding ValidationErrors of
                # type type_error.none.not_allowed.
                for kwarg, value in kwargs.items():
                    if value.__class__.__class__ is PartialModelMetaclass:
                        kwargs[kwarg] = value.dict()
                    elif isinstance(value, (tuple, list)):
                        kwargs[kwarg] = value.__class__(
                            v.dict()
                            if v.__class__.__class__ is PartialModelMetaclass
                            else v
                            for v in value
                        )

                # Validation is performed in __init__, for which all fields are now optional
                cls_init(self, *args, **kwargs)
                # Restore requiredness
                optionalize(fields, restore=True)

        setattr(cls, "__init__", __init__)

        # Exclude unset (`None`) from dict(), which isn't allowed in the schema
        # but will be the default for non-required fields. This enables
        # PartialModel(**PartialModel().dict()) to work correctly.

        # cls_dict = cls.dict

        # def dict_exclude_unset(
        #     self: BaseModel, *args: Any, exclude_unset: bool = None, **kwargs: Any
        # ) -> Dict[str, Any]:
        #     return cls_dict(self, *args, **kwargs, exclude_unset=exclude_unset)

        # cls.dict = dict_exclude_unset

        return cls
