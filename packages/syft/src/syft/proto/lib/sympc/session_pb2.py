# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proto/lib/sympc/session.proto
"""Generated protocol buffer code."""
# third party
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


# syft absolute
from syft.proto.core.node.common import (
    client_pb2 as proto_dot_core_dot_node_dot_common_dot_client__pb2,
)
from syft.proto.lib.python import dict_pb2 as proto_dot_lib_dot_python_dot_dict__pb2
from syft.proto.lib.sympc import (
    protocol_pb2 as proto_dot_lib_dot_sympc_dot_protocol__pb2,
)

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x1dproto/lib/sympc/session.proto\x12\x0esyft.lib.sympc\x1a#proto/core/node/common/client.proto\x1a\x1bproto/lib/python/dict.proto\x1a\x1eproto/lib/sympc/protocol.proto"\xfe\x01\n\nMPCSession\x12\x0c\n\x04uuid\x18\x01 \x01(\t\x12\x0c\n\x04rank\x18\x02 \x01(\x05\x12\x11\n\tring_size\x18\x03 \x01(\x0c\x12\x12\n\nnr_parties\x18\x04 \x01(\x0c\x12%\n\x06\x63onfig\x18\x05 \x01(\x0b\x32\x15.syft.lib.python.Dict\x12.\n\x07parties\x18\x06 \x03(\x0b\x32\x1d.syft.core.node.common.Client\x12*\n\x03ttp\x18\x07 \x01(\x0b\x32\x1d.syft.core.node.common.Client\x12*\n\x08protocol\x18\x08 \x01(\x0b\x32\x18.syft.lib.sympc.protocolb\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(
    DESCRIPTOR, "proto.lib.sympc.session_pb2", globals()
)
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _MPCSESSION._serialized_start = 148
    _MPCSESSION._serialized_end = 402
# @@protoc_insertion_point(module_scope)
