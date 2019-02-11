# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
import pss_pb2 as pss__pb2


class pssStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.read = channel.unary_unary(
        '/pss/read',
        request_serializer=pss__pb2.ReadRequest.SerializeToString,
        response_deserializer=pss__pb2.Response.FromString,
        )
    self.write = channel.unary_unary(
        '/pss/write',
        request_serializer=pss__pb2.WriteRequest.SerializeToString,
        response_deserializer=pss__pb2.Status.FromString,
        )
    self.process = channel.unary_unary(
        '/pss/process',
        request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
        response_deserializer=pss__pb2.Status.FromString,
        )


class pssServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def read(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def write(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def process(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_pssServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'read': grpc.unary_unary_rpc_method_handler(
          servicer.read,
          request_deserializer=pss__pb2.ReadRequest.FromString,
          response_serializer=pss__pb2.Response.SerializeToString,
      ),
      'write': grpc.unary_unary_rpc_method_handler(
          servicer.write,
          request_deserializer=pss__pb2.WriteRequest.FromString,
          response_serializer=pss__pb2.Status.SerializeToString,
      ),
      'process': grpc.unary_unary_rpc_method_handler(
          servicer.process,
          request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
          response_serializer=pss__pb2.Status.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'pss', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
