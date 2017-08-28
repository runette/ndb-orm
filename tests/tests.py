#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase, main

import binascii
import ndb_orm as ndb
from google.cloud.proto.datastore.v1 import entity_pb2

class Person(ndb.Model):
    name = ndb.TextProperty(indexed=False, compressed=True)

class ProtocolBuffer(TestCase):

    def test_from_stringified(self):

        # hexlified protocolbuffer of Person(name='Hallo')
        pb_binary_string = binascii.unhexlify("0a250a10120e616161616161616161616161616112110a06506572736f6e10808080808080800a1a1d0a046e616d651215701692010d789cf348ccc9c90700057c01f1980101")

        pb = entity_pb2.Entity()
        pb.ParseFromString(pb_binary_string)
        model = ndb.model_from_protobuf(pb)

        self.assertEqual(model._class_name(), "Person")
        self.assertEqual(model.name, "Hallo")

    def test_complex_model(self):

        import datetime
        import binascii
        from protorpc import messages
        from . import person_pb2
        from .gcloud_credentials import EmulatorCredentials
        from google.cloud import datastore
        from google.cloud.proto.datastore.v1 import entity_pb2

        namespace = "your-namespace"

        ndb.model.ENABLE_PICKLE_LOADS = True # might be dangerous in production

        class Items(ndb.Model):
            has_hat = ndb.BooleanProperty("hh")
            number_of_socks = ndb.IntegerProperty("ns")

        class Gender(messages.Enum):
            male = 1
            female = 2
            neutral = 3

        person = person_pb2.Person()
        person.id = 1234
        person.name = "John Doe"
        person.email = "jdoe@example.com"
        phone = person.phones.add()
        phone.number = "555-4321"
        phone.type = person_pb2.Person.HOME

        class Human2(ndb.Model):
            name = ndb.StringProperty("na", indexed=True)
            gender = ndb.msgprop.EnumProperty(Gender, "g", required=True, indexed=True)
            age = ndb.IntegerProperty("ag", indexed=False)
            items = ndb.StructuredProperty(Items, "i", required=True)
            numbers = ndb.JsonProperty('json', indexed=False)
            description = ndb.TextProperty("t", indexed=False)
            description2 = ndb.TextProperty("t2", compressed=True, indexed=False)
            meters_tall = ndb.FloatProperty("mtrs", indexed=False)
            datetime_of_birth = ndb.DateTimeProperty("dtb", indexed=False)
            date_of_birth = ndb.DateProperty("db", indexed=False)
            time_of_birth = ndb.TimeProperty("tb", indexed=False)
            hobbies = ndb.StringProperty('hob', repeated=True, indexed=False)
            pickle = ndb.PickleProperty('pi', indexed=False)
            binary = ndb.BlobProperty("bi", indexed=False)
            home = ndb.GeoPtProperty("ho", indexed=False)
            generic = ndb.GenericProperty("gen", indexed=False)
            model = ndb.LocalStructuredProperty(Items, "mo", indexed=False)
            person_details = ndb.msgprop.MessageProperty(person_pb2.Person, "pd")

            number_of_hobbies = ndb.ComputedProperty(name="num_hob", func=lambda self: len(self.hobbies), indexed=False)
            default_info = ndb.StringProperty("di", indexed=False, default='unknown')
            update = ndb.DateTimeProperty("up", indexed=False, auto_now=True)

            def _pre_put_hook(self):
                pass
                #print("_pre_put_hook")

        human = Human2(
            name='Arthur Dent',
            gender=Gender.male,
            age=42,
            items=Items(has_hat=True, number_of_socks=3, namespace=namespace),
            numbers=[12, 13, 14],
            description="a real man",
            description2="a real man, oh yeah",
            meters_tall=1.82,
            datetime_of_birth=datetime.datetime(2017, 8, 26, 15, 10, 42, 123456),
            date_of_birth=datetime.datetime(2017, 8, 26, 15, 10, 42, 123456).date(),
            time_of_birth=datetime.datetime(2017, 8, 26, 15, 10, 42, 123456).time(),
            hobbies=[u"football", u"tv"],
            pickle=[{"football_at": datetime.datetime(2017, 8, 26, 15, 10, 42, 123456)}],
            binary=binascii.unhexlify("61626300"),
            home=ndb.GeoPt("52.37, 4.88"),
            generic=7,
            #model=Items(has_hat=True, number_of_socks=3, namespace=namespace).to_dict(),
            model=Items(has_hat=True, number_of_socks=3, namespace=namespace),
            person_details=person,
            namespace=namespace
        )

        client = datastore.Client(project="kunstakrobaten", credentials=EmulatorCredentials())

        # convert to protocolbuffer
        pb = ndb.model_to_protobuf(human, project=client.project)
        #print(pb)

        # serialize to binary string
        pb_binary_string = pb.SerializeToString()

        human_recovered = human
        # create protocolbuffer enitiy out of binary string
        pb = entity_pb2.Entity()
        pb.ParseFromString(pb_binary_string)
        human_recovered = ndb.model_from_protobuf(pb)

        # now do the tests
        self.assertEqual(human_recovered.name, 'Arthur Dent')
        self.assertEqual(human_recovered.gender, Gender.male)
        self.assertEqual(human_recovered.age, 42)
        self.assertEqual(human_recovered.items.has_hat, True)
        self.assertEqual(human_recovered.items.number_of_socks, 3)
        self.assertEqual(human_recovered.numbers, [12, 13, 14])
        self.assertEqual(human_recovered.description, "a real man")
        self.assertEqual(human_recovered.description2, "a real man, oh yeah")
        self.assertAlmostEqual(human_recovered.meters_tall, 1.82)
        # DateTime always have a timezone attached
        self.assertEqual(human_recovered.datetime_of_birth.replace(tzinfo=None), datetime.datetime(2017, 8, 26, 15, 10, 42, 123456))
        self.assertEqual(human_recovered.date_of_birth, datetime.datetime(2017, 8, 26, 15, 10, 42, 123456).date())
        self.assertEqual(human_recovered.time_of_birth, datetime.datetime(2017, 8, 26, 15, 10, 42, 123456).time())
        self.assertEqual(human_recovered.hobbies, [u"football", u"tv"])
        self.assertEqual(human_recovered.pickle[0]["football_at"], datetime.datetime(2017, 8, 26, 15, 10, 42, 123456))
        self.assertEqual(human_recovered.binary, binascii.unhexlify("61626300"))
        self.assertAlmostEqual(human_recovered.home.lat, 52.37)
        self.assertAlmostEqual(human_recovered.home.lon, 4.88)
        self.assertEqual(human_recovered.generic, 7)
        self.assertEqual(human_recovered.model.has_hat, True)
        self.assertEqual(human_recovered.model.number_of_socks, 3)
        self.assertEqual(human_recovered.person_details.phones[0].number, "555-4321")

        # these were set automatically
        self.assertEqual(human_recovered.number_of_hobbies, 2)
        self.assertEqual(human_recovered.default_info, "unknown")
        self.assertEqual(isinstance(human_recovered.update, datetime.date), True)

        ndb.model.ENABLE_PICKLE_LOADS = False

    def test_complex_model2(self):
        import binascii
        import datetime
        from protorpc import messages
        #from google.appengine.ext.ndb import msgprop
        from ndb_orm import msgprop


        class Items(ndb.Model):
            has_hat = ndb.BooleanProperty("hh")
            number_of_socks = ndb.IntegerProperty("ns")

        class Gender(messages.Enum):
            male = 1
            female = 2
            neutral = 3

        class Human(ndb.Model):
            name = ndb.StringProperty("na", indexed=True)
            gender = msgprop.EnumProperty(Gender, "g", required=True, indexed=True)
            age = ndb.IntegerProperty("ag", indexed=False)
            items = ndb.StructuredProperty(Items, "i", required=True)
            numbers = ndb.JsonProperty('json', indexed=False)
            description = ndb.TextProperty("t", indexed=False)
            description2 = ndb.TextProperty("t2", compressed=True, indexed=False)
            meters_tall = ndb.FloatProperty("mtrs", indexed=False)
            datetime_of_birth = ndb.DateTimeProperty("dtb", indexed=False)
            date_of_birth = ndb.DateProperty("db", indexed=False)
            time_of_birth = ndb.TimeProperty("tb", indexed=False)
            hobbies = ndb.StringProperty('hob', repeated=True, indexed=False)
            pickle = ndb.PickleProperty('pi', indexed=False)
            binary = ndb.BlobProperty("bi", indexed=False)
            home = ndb.GeoPtProperty("ho", indexed=False)
            generic = ndb.GenericProperty("gen", indexed=False)
            model = ndb.LocalStructuredProperty(Items, "mo", indexed=False)

            number_of_hobbies = ndb.ComputedProperty(name="num_hob", func=lambda self: len(self.hobbies), indexed=False)
            default_info = ndb.StringProperty("di", indexed=False, default='unknown')
            update = ndb.DateTimeProperty("up", indexed=False, auto_now=True)

        # the entity was created from within app engine standard with the code below
        # and the the protocolbuffer was fetch with google-cloud-datastore and hexlified
        pb_binary_string = binascii.unhexlify('0a240a10120e6b756e7374616b726f626174656e12100a0548756d616e108080808080e4910a1a4b0a027069124592013f80025d71017d7102550b666f6f7462616c6c5f61747103636461746574696d650a6461746574696d650a7104550a07e1081a0f0a2a01e2408552710573612e9801011a1f0a026d6f121932141a080a026e73120210031a080a026868120208019801011a100a026269120a920104616263009801011a140a027462120e520908f2aa03108094ef3a9801011a140a026e61120e8a010b4172746875722044656e741a1a0a046a736f6e121292010c5b31322c2031332c2031345d9801011a100a076e756d5f686f62120510029801011a0a0a04692e6e73120210031a0c0a0367656e120510079801011a0a0a04692e6868120208011a150a026469120f700f8a0107756e6b6e6f776e9801011a110a026462120b52060880f482cd059801011a270a03686f6212204a1e0a10700f8a0108666f6f7462616c6c9801010a0a700f8a010274769801011a0b0a0261671205102a9801011a1d0a02686f12174212098fc2f5285c2f4a401185eb51b81e8513409801011a070a0167120210011a290a0274321223701692011b789c4b54284a4dcc51c84dccd351c8cf50a84c4dcc00003f14066c9801011a140a046d747273120c191f85eb51b81efd3f9801011a170a036474621210520b08f29e86cd05108094ef3a9801011a170a0275701211520c08abc791cd051080abfd8e039801011a170a01741212700f8a010a61207265616c206d616e980101')

#         human = Human(
#             name='Arthur Dent',
#             gender=Gender.male,
#             age=42,
#             items=Items(has_hat=True, number_of_socks=3), #namespace=namespace),
#             numbers=[12, 13, 14],
#             description="a real man",
#             description2="a real man, oh yeah",
#             meters_tall=1.82,
#             datetime_of_birth=datetime.datetime(2017, 8, 26, 15, 10, 42, 123456),
#             date_of_birth=datetime.datetime(2017, 8, 26, 15, 10, 42, 123456).date(),
#             time_of_birth=datetime.datetime(2017, 8, 26, 15, 10, 42, 123456).time(),
#             hobbies=[u"football", u"tv"],
#             pickle=[{"football_at": datetime.datetime(2017, 8, 26, 15, 10, 42, 123456)}],
#             binary=binascii.unhexlify("61626300"),
#             home=ndb.GeoPt("52.37, 4.88"),
#             generic=7,
#             model=Items(has_hat=True, number_of_socks=3), #namespace=namespace),
#         )
#         human.put()

        pb = entity_pb2.Entity()
        pb.ParseFromString(pb_binary_string)
        human_recovered = ndb.model_from_protobuf(pb)

        # now do the tests
        self.assertEqual(human_recovered.name, 'Arthur Dent')
        self.assertEqual(human_recovered.gender, Gender.male)
        self.assertEqual(human_recovered.age, 42)
        self.assertEqual(human_recovered.items.has_hat, True)
        self.assertEqual(human_recovered.items.number_of_socks, 3)
        self.assertEqual(human_recovered.numbers, [12, 13, 14])
        self.assertEqual(human_recovered.description, "a real man")
        self.assertEqual(human_recovered.description2, "a real man, oh yeah")
        self.assertAlmostEqual(human_recovered.meters_tall, 1.82)
        # DateTime always have a timezone attached
        self.assertEqual(human_recovered.datetime_of_birth.replace(tzinfo=None), datetime.datetime(2017, 8, 26, 15, 10, 42, 123456))
        self.assertEqual(human_recovered.date_of_birth, datetime.datetime(2017, 8, 26, 15, 10, 42, 123456).date())
        self.assertEqual(human_recovered.hobbies, [u"football", u"tv"])
        # following is a PickleProperty and thus not recoverable from python3
        #self.assertEqual(human_recovered.pickle[0]["football_at"], datetime.datetime(2017, 8, 26, 15, 10, 42, 123456))
        self.assertEqual(human_recovered.binary, binascii.unhexlify("61626300"))
        self.assertAlmostEqual(human_recovered.home.lat, 52.37)
        self.assertAlmostEqual(human_recovered.home.lon, 4.88)
        self.assertEqual(human_recovered.generic, 7)
        self.assertEqual(human_recovered.model.has_hat, True)
        self.assertEqual(human_recovered.model.number_of_socks, 3)

        # these were set automatically
        self.assertEqual(human_recovered.number_of_hobbies, 2)
        self.assertEqual(human_recovered.default_info, "unknown")
        self.assertEqual(isinstance(human_recovered.update, datetime.date), True)

if __name__ == '__main__':
    main()