# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proto/core/node/common/action/get_set_static_attribute.proto
"""Generated protocol buffer code."""
# third party
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


# syft absolute
from syft.proto.core.common import (
    common_object_pb2 as proto_dot_core_dot_common_dot_common__object__pb2,
)
from syft.proto.core.io import address_pb2 as proto_dot_core_dot_io_dot_address__pb2
from syft.proto.core.pointer import (
    pointer_pb2 as proto_dot_core_dot_pointer_dot_pointer__pb2,
)

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n<proto/core/node/common/action/get_set_static_attribute.proto\x12\x1csyft.core.node.common.action\x1a%proto/core/common/common_object.proto\x1a\x1bproto/core/io/address.proto\x1a proto/core/pointer/pointer.proto"\xe6\x01\n\x1bGetSetStaticAttributeAction\x12\x0c\n\x04path\x18\x01 \x01(\t\x12+\n\x07set_arg\x18\x02 \x01(\x0b\x32\x1a.syft.core.pointer.Pointer\x12-\n\x0eid_at_location\x18\x03 \x01(\x0b\x32\x15.syft.core.common.UID\x12&\n\x07\x61\x64\x64ress\x18\x04 \x01(\x0b\x32\x15.syft.core.io.Address\x12%\n\x06msg_id\x18\x05 \x01(\x0b\x32\x15.syft.core.common.UID\x12\x0e\n\x06\x61\x63tion\x18\x06 \x01(\x05\x62\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(
    DESCRIPTOR, "proto.core.node.common.action.get_set_static_attribute_pb2", globals()
)
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _GETSETSTATICATTRIBUTEACTION._serialized_start = 197
    _GETSETSTATICATTRIBUTEACTION._serialized_end = 427
# @@protoc_insertion_point(module_scope)