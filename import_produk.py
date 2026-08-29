
from django.core.management.base import BaseCommand
from master.models import MasterProduk

class Command(BaseCommand):
    help = 'Mengimpor data produk internal dari dictionary'

    def handle(self, *args, **options):
        data_produk = {
                "bio_grey": "BIO GREY",
                "bio_grey_sh": "BIO GREY SH",
                "black": "BLACK",
                "black_lx": "BLACK LX",
                "black_sp": "BLACK SP",
                "black_sp_type_lx": "BLACK SP TYPE LX",
                "black_wb": "BLACK WB",
                "blue_cw": "BLUE CW",
                "blue_cw_13": "BLUE CW 13",
                "blue_cw_13_std": "BLUE CW 13 STD",
                "blue_cw_a": "BLUE CW -A",
                "blue_cw_sl": "BLUE CW SL",
                "blue_cw_sp": "BLUE CW SP",
                "blue_cw_tb": "BLUE CW TB",
                "blue_dongker": "BLUE DONGKER",
                "blue_pg": "BLUE PG",
                "blue_wb": "BLUE WB",
                "bone_white" : "BONE WHITE",
                "classical_yellow": "CLASSICAL YELLOW",
                "cosca_green": "COSCA GREEN",   
                "cosca_green_sh": "COSCA GREEN SH",
                "coffee_brown": "COFFEE BROWN",
                "cyan_blue": "CYAN BLUE",
                "cream_cpr" : "CREAM CPR",
                "general_blue": "GENERAL BLUE",
                "general_red": "GENERAL RED",
                "golden_yellow": "GOLDEN YELLOW",
                "golden_yellow_or" : "GOLDEN YELLOW OR",
                "goden_yellow_tb" : "GOLDEN YELLOW TB",
                "green_hn": "GREEN HN",
                "green_lime": "GREEN LIME",
                "green_lime_rm": "GREEN LIME RM",
                "green_sc" : "GREEN SC",
                "green_wb": "GREEN WB",
                "grey_manhaton_sh": "GREY MANHATON SH",
                "grey_pd": "GREY PD",
                "grey_mjf": "GREY MJF",
                "grey_sh": "GREY SH",
                "grey_utm": "GREY UTM",
                "grey_iwb": "GREY IWB",
                "grey_iwb_i": "GREY IWB I",
                "grey_wb_b": "GREY WB - B",
                "ground_red": "GROUND RED",
                "ivory_kd": "IVORY KD",
                "ivory_dk": "IVORY DK",
                "ivory_toto": "IVORY TOTO",
                "light_green": "LIGHT GREEN",
                "light_grey": "LIGHT GREY",
                "lighted_orange": "LIGHTED ORANGE",
                "lighted_orange_tb": "LIGHTED ORANGE TB",
                "mouse_grey": "MOUSE GREY",
                "natural_blue": "NATURAL BLUE",
                "natural_white_t9010": "NATURAL WHITE T9010",
                "orange_pd" : "ORANGE PD",
                "orange_sc": "ORANGE SC",
                "orange_tb": "ORANGE TB",
                "pasta_green_wb": "PASTA GREEN WB",
                "pasta_white_ces": "PASTA WHITE CES",
                "pastel_white_bright": "PASTEL WHITE BR",
                "pastel_pink" : "PASTEL PINK",
                "pastel_pink_sh": "PASTEL PINK SH",
                "pink_sc": "PINK SC",
                "rose_pink": "ROSE PINK",
                "signal_red": "SIGNAL RED",
                "sgnal_red_tb": "SIGNAL RED TB",
                "signal_yellow": "SIGNAL YELLOW",
                "sky_blue": "SKY BLUE",
                "soft_grey": "SOFT GREY",
                "sunshine_yellow": "SUNSHINE YELLOW",
                "super_white": "SUPER WHITE",
                "super_white_A": "SUPER WHITE -A",
                "super_white_C": "SUPER WHITE -C",
                "super_white_sc": "SUPER WHITE SC",
                "super_white_spl": "SUPER WHITE SPL",
                "super_white_tb": "SUPER WHITE TB",
                "super_white_toto": "SUPER WHITE TOTO",
                "super_white_or" : "SUPER WHITE OR",
                "suzuki_blue": "SUZUKI BLUE",
                "suzuki_blue_rm": "SUZUKI BLUE RM",
                "sweet_green": "SWEET GREEN",
                "sweet_green_op": "SWEET GREEN OP",
                "sweet_red": "SWEET RED",
                "tosca_green": "TOSCA GREEN",
                "union_blue": "UNION BLUE",
                "union_blue_a": "UNION BLUE -A",
                "union_blue_tb": "UNION BLUE TB",
                "union_green": "UNION GREEN",
                "violet_sc": "VIOLET SC",
                "vr_blue": "VR BLUE",
                "yellow_sc": "YELLOW SC",
                "yellow_wb": "YELLOW WB"
        }

        success_count = 0
        for kode, nama in data_produk.items():
            MasterProduk.objects.update_or_create(
                id=kode,
                defaults={'nama_item': nama}
            )
            success_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Berhasil memproses {success_count} data produk!')
        )
