# pragma: no cover
from time import perf_counter

from django.test import TestCase

try:
    import enum_properties
    ENUM_PROPERTIES_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    ENUM_PROPERTIES_INSTALLED = False


if ENUM_PROPERTIES_INSTALLED:

    from django_enum.tests.enum_prop.enums import (
        BigIntEnum,
        BigPosIntEnum,
        Constants,
        DJIntEnum,
        DJTextEnum,
        IntEnum,
        PosIntEnum,
        SmallIntEnum,
        SmallPosIntEnum,
        TextEnum,
    )
    from django_enum.tests.enum_prop.models import (
        EnumTester,
        NoCoercePerfCompare,
        PerfCompare,
        SingleEnumPerf,
        SingleFieldPerf,
        SingleNoCoercePerf,
    )

    class PerformanceTest(TestCase):
        """
        We intentionally test bulk operations performance because thats what
        we're most interested in with operations at this scale
        """

        CHUNK_SIZE = 2048
        COUNT = CHUNK_SIZE * 25
        MODEL_CLASS = EnumTester

        create_queue = []

        def create(self, obj=None):
            if obj:
                self.create_queue.append(obj)
            if (obj is None and self.create_queue) or len(
                    self.create_queue) >= self.CHUNK_SIZE:
                self.create_queue[0].__class__.objects.bulk_create(
                    self.create_queue)
                self.create_queue.clear()

        def test_benchmark(self):
            enum_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    self.MODEL_CLASS(
                        small_pos_int=SmallPosIntEnum.VAL2,
                        small_int='Value -32768',
                        pos_int=2147483647,
                        int=-2147483648,
                        big_pos_int='Value 2147483648',
                        big_int='VAL2',
                        constant='φ',
                        text='V TWo',
                        dj_int_enum=3,
                        dj_text_enum=DJTextEnum.A,
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=SmallPosIntEnum.VAL2
                    )
                )
            self.create()
            enum_stop = perf_counter()

            delete_mark = self.MODEL_CLASS.objects.last().pk

            choice_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    PerfCompare(
                        small_pos_int=2,
                        small_int=-32768,
                        pos_int=2147483647,
                        int=-2147483648,
                        big_pos_int=2147483648,
                        big_int=2,
                        constant=1.61803398874989484820458683436563811,
                        text='V22',
                        dj_int_enum=3,
                        dj_text_enum='A',
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=2
                    )
                )
            self.create()
            choice_stop = perf_counter()

            enum_direct_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    self.MODEL_CLASS(
                        small_pos_int=SmallPosIntEnum.VAL2,
                        small_int=SmallIntEnum.VALn1,
                        pos_int=PosIntEnum.VAL3,
                        int=IntEnum.VALn1,
                        big_pos_int=BigPosIntEnum.VAL3,
                        big_int=BigIntEnum.VAL2,
                        constant=Constants.GOLDEN_RATIO,
                        text=TextEnum.VALUE2,
                        dj_int_enum=DJIntEnum.THREE,
                        dj_text_enum=DJTextEnum.A,
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=SmallPosIntEnum.VAL2
                    )
                )
            self.create()
            enum_direct_stop = perf_counter()
            self.MODEL_CLASS.objects.filter(pk__gt=delete_mark).delete()

            no_coerce_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    NoCoercePerfCompare(
                        small_pos_int=2,
                        small_int=-32768,
                        pos_int=2147483647,
                        int=-2147483648,
                        big_pos_int=2147483648,
                        big_int=2,
                        constant=1.61803398874989484820458683436563811,
                        text='V22',
                        dj_int_enum=3,
                        dj_text_enum='A',
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=2
                    )
                )
            self.create()
            no_coerce_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            enum_direct_time = enum_direct_stop - enum_direct_start
            no_coerce_time = no_coerce_stop - no_coerce_start
            # flag if performance degrades signficantly - running about 2x for big lookups
            self.assertTrue((enum_time / choice_time) < 3)
            self.assertTrue((enum_direct_time / choice_time) < 2.5)
            self.assertTrue((no_coerce_time / choice_time) < 2.5)
            print(
                f'(EnumTester) Bulk Create -> '
                f'EnumField: {enum_time} '
                f'EnumField (direct): {enum_direct_time} '
                f'EnumField (no coerce): {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )

            self.assertEqual(self.MODEL_CLASS.objects.count(), self.COUNT)
            self.assertEqual(PerfCompare.objects.count(), self.COUNT)
            self.assertEqual(NoCoercePerfCompare.objects.count(), self.COUNT)

            enum_start = perf_counter()
            for _ in self.MODEL_CLASS.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for _ in PerfCompare.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            choice_stop = perf_counter()

            no_coerce_start = perf_counter()
            for _ in NoCoercePerfCompare.objects.iterator(
                    chunk_size=self.CHUNK_SIZE):
                continue
            no_coerce_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            no_coerce_time = no_coerce_stop - no_coerce_start
            self.assertTrue((enum_time / choice_time) < 7)
            self.assertTrue((no_coerce_time / choice_time) < 4)
            print(
                f'(EnumTester) Chunked Read -> '
                f'EnumField: {enum_time} '
                f'No Coercion: {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )

        def test_single_field_benchmark(self):

            enum_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(SingleEnumPerf(small_pos_int=0))
            self.create()
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(SingleFieldPerf(small_pos_int=0))
            self.create()
            choice_stop = perf_counter()

            no_coerce_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(SingleNoCoercePerf(small_pos_int=0))
            self.create()
            no_coerce_end = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            no_coerce_time = no_coerce_end - no_coerce_start

            print(
                f'(Single Field) Bulk Creation -> '
                f'EnumField: {enum_time} '
                f'No Coercion: {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )
            # Enum tends to be about ~12% slower
            self.assertTrue((enum_time / choice_time) < 1.8)
            self.assertTrue((no_coerce_time / choice_time) < 1.7)

            enum_start = perf_counter()
            for _ in SingleEnumPerf.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for _ in SingleFieldPerf.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            choice_stop = perf_counter()

            no_coerce_start = perf_counter()
            for _ in SingleNoCoercePerf.objects.iterator(
                    chunk_size=self.CHUNK_SIZE):
                continue
            no_coerce_end = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            no_coerce_time = no_coerce_end - no_coerce_start

            print(
                f'(Single Field) Chunked Read -> '
                f'EnumField: {enum_time} '
                f'No Coercion: {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )
            # tends to be about 1.8x slower
            self.assertTrue((enum_time / choice_time) < 2.5)
            self.assertTrue((no_coerce_time / choice_time) < 2)
