# pragma: no cover
from time import perf_counter
from django_enum.tests.benchmark import enums as benchmark_enums
from django_enum.tests.benchmark import models as benchmark_models
from django.test import TestCase
import random
from django.db import connection
from functools import reduce
from operator import or_, and_
from django.db.models import Q

try:
    import enum_properties
    ENUM_PROPERTIES_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    ENUM_PROPERTIES_INSTALLED = False


class BulkCreateMixin:

    CHUNK_SIZE = 2048

    create_queue = {}

    def create(self, obj=None):
        if obj:
            self.create_queue.setdefault(obj.__class__, []).append(obj)
        for Model, queue in self.create_queue.items():
            if (
                (obj is None and queue) or
                len(queue) >= self.CHUNK_SIZE
            ):
                Model.objects.bulk_create(queue)
                queue.clear()


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

    class PerformanceTest(BulkCreateMixin, TestCase):
        """
        We intentionally test bulk operations performance because thats what
        we're most interested in with operations at this scale
        """

        CHUNK_SIZE = 2048
        COUNT = CHUNK_SIZE * 25
        MODEL_CLASS = EnumTester

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
            print(
                f'(EnumTester) Bulk Create -> '
                f'EnumField: {enum_time} '
                f'EnumField (direct): {enum_direct_time} '
                f'EnumField (no coerce): {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )

            self.assertTrue((enum_time / choice_time) < 4)
            self.assertTrue((enum_direct_time / choice_time) < 3)
            self.assertTrue((no_coerce_time / choice_time) < 3)
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


class FlagBenchmarks(BulkCreateMixin, TestCase):

    COUNT = 10000

    FLAG_MODELS = [
        mdl for name, mdl in benchmark_models.__dict__.items()
        if hasattr(mdl, 'FLAG')
    ]
    BOOL_MODELS = [
        mdl for name, mdl in benchmark_models.__dict__.items()
        if hasattr(mdl, 'BOOL')
    ]

    def setUp(self):

        for FlagModel, BoolModel in zip(self.FLAG_MODELS, self.BOOL_MODELS):
            for idx in range(0, self.COUNT):
                assert FlagModel.num_flags == BoolModel.num_flags
                mask = random.getrandbits(FlagModel.num_flags)
                self.create(FlagModel(flags=mask))
                self.create(BoolModel(**{
                    f'flg_{flg}': bool(mask & (1 << flg) != 0)
                    for flg in range(0, BoolModel.num_flags)
                }))

        self.create()

    def get_table_size(self, cursor, table, total=True):
        cursor.execute(
            f"SELECT pg_size_pretty(pg{'_total' if total else ''}"
            f"_relation_size('{table}'));"
        )
        size_bytes, scale = cursor.fetchone()[0].lower().split()
        size_bytes = float(size_bytes)
        if 'k' in scale:
            size_bytes *= 1024
        elif 'm' in scale:
            size_bytes *= 1024 * 1024
        elif 'g' in scale:
            size_bytes *= 1024 * 1024 * 1024

        return size_bytes

    def get_column_size(self, cursor, table, column):
        cursor.execute(
            f"SELECT sum(pg_column_size({column})) FROM {table};"
        )
        return cursor.fetchone()[0]

    def test_size_benchmark(self):

        table_sizes = {}
        total_table_sizes = {}
        column_sizes = {}

        with connection.cursor() as cursor:
            for FlagModel, BoolModel in zip(self.FLAG_MODELS, self.BOOL_MODELS):
                assert FlagModel.num_flags == BoolModel.num_flags
                flag_size = self.get_table_size(cursor, FlagModel._meta.db_table, total=False)
                bool_size = self.get_table_size(cursor, BoolModel._meta.db_table, total=False)
                total_flag_size = self.get_table_size(cursor, FlagModel._meta.db_table, total=True)
                total_bool_size = self.get_table_size(cursor, BoolModel._meta.db_table, total=True)
                flag_col_size = self.get_column_size(cursor, FlagModel._meta.db_table, FlagModel._meta.get_field('flags').column)
                bool_col_size = sum([
                    self.get_column_size(
                        cursor,
                        BoolModel._meta.db_table,
                        BoolModel._meta.get_field(f'flg_{flg}').column
                    ) for flg in range(0, BoolModel.num_flags)
                ])
                table_sizes[FlagModel.num_flags] = (bool_size - flag_size) / self.COUNT
                total_table_sizes[FlagModel.num_flags] = (total_bool_size - total_flag_size) / self.COUNT
                column_sizes[FlagModel.num_flags] = (bool_col_size - flag_col_size) / self.COUNT

        print([table_sizes[num_flags] for num_flags in sorted(table_sizes.keys())])
        print('--------------------------------')
        print([total_table_sizes[num_flags] for num_flags in sorted(total_table_sizes.keys())])
        print('--------------------------------')
        print([column_sizes[num_flags] for num_flags in sorted(column_sizes.keys())])

    def test_query_performance(self):

        has_any_flag_count = {}
        has_all_flag_count = {}
        has_any_flag_load = {}
        has_all_flag_load = {}

        has_any_bool_count = {}
        has_all_bool_count = {}
        has_any_bool_load = {}
        has_all_bool_load = {}

        with connection.cursor() as cursor:
            for FlagModel, BoolModel in zip(self.FLAG_MODELS, self.BOOL_MODELS):
                assert FlagModel.num_flags == BoolModel.num_flags

                mask = random.getrandbits(FlagModel.num_flags)
                if not mask:
                    mask = 1
                mask_en = FlagModel._meta.get_field('flags').enum(mask)

                flag_any_q = FlagModel.objects.filter(flags__has_any=mask_en)
                flag_all_q = FlagModel.objects.filter(flags__has_all=mask_en)

                bool_q = [
                    Q(**{f'flg_{flg}': bool(mask & (1 << flg) != 0)})
                    for flg in range(0, BoolModel.num_flags)
                    if bool(mask & (1 << flg) != 0)
                ]
                bool_any_q = (
                    BoolModel.objects.filter(reduce(or_, bool_q))
                    if bool_q else BoolModel.objects.none()
                )

                bool_all_q = (
                    BoolModel.objects.filter(reduce(and_, bool_q))
                    if bool_q else BoolModel.objects.none()
                )

                start = perf_counter()
                flag_any_count = flag_any_q.count()
                has_any_flag_count[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_any_count = bool_any_q.count()
                has_any_bool_count[BoolModel.num_flags] = perf_counter() - start

                try:
                    # make sure our queries are equivalent
                    self.assertEqual(flag_any_count, bool_any_count)
                except AssertionError:
                    import ipdb
                    ipdb.set_trace()

                start = perf_counter()
                flag_all_count = flag_all_q.count()
                has_all_flag_count[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_all_count = bool_all_q.count()
                has_all_bool_count[BoolModel.num_flags] = perf_counter() - start

                # make sure our queries are equivalent
                self.assertEqual(flag_all_count, bool_all_count)

                start = perf_counter()
                flag_any_list = list(flag_any_q.all())
                has_any_flag_load[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_any_list = list(bool_any_q.all())
                has_any_bool_load[BoolModel.num_flags] = perf_counter() - start

                # make sure our queries are equivalent
                self.assertEqual(len(flag_any_list), len(bool_any_list))

                start = perf_counter()
                flag_all_list = list(flag_all_q.all())
                has_all_flag_load[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_all_list = list(bool_all_q.all())
                has_all_bool_load[BoolModel.num_flags] = perf_counter() - start

                # make sure our queries are equivalent
                self.assertEqual(len(flag_all_list), len(bool_all_list))

        num_flags = sorted(has_any_flag_count.keys())

        has_any_count_diff = [
            has_any_bool_count[flg] - has_any_flag_count[flg]
            for flg in num_flags
        ]
        has_all_count_diff = [
            has_all_bool_count[flg] - has_all_flag_count[flg]
            for flg in num_flags
        ]

        has_any_load_diff = [
            has_any_bool_load[flg] - has_any_flag_load[flg]
            for flg in num_flags
        ]
        has_all_load_diff = [
            has_all_bool_load[flg] - has_all_flag_load[flg]
            for flg in num_flags
        ]

        # print(has_any_count_diff)
        # print('--------------------------------')
        # print(has_all_count_diff)
        # print('--------------------------------')
        # print(has_any_load_diff)
        # print('--------------------------------')
        # print(has_all_load_diff)

        has_any_count_tpl = [
            (has_any_bool_count[flg],  has_any_flag_count[flg])
            for flg in num_flags
        ]
        has_all_count_tpl = [
            (has_all_bool_count[flg],  has_all_flag_count[flg])
            for flg in num_flags
        ]

        has_any_load_tpl = [
            (has_any_bool_load[flg], has_any_flag_load[flg])
            for flg in num_flags
        ]
        has_all_load_tpl = [
            (has_all_bool_load[flg], has_all_flag_load[flg])
            for flg in num_flags
        ]

        print('------------ has_any_cnt ----------------')
        print(has_any_count_tpl)
        print('------------ has_all_cnt ----------------')
        print(has_all_count_tpl)
        print('------------ has_any_load ---------------')
        print(has_any_load_tpl)
        print('------------ has_all_load ---------------')
        print(has_all_load_tpl)