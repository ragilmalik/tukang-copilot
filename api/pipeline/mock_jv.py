"""Basa Jawa (ngoko, as spoken around Semarang) for every demo answer in mock.py, keyed by the Indonesian text.

Before v1.22 the demo answers fell back to Bahasa Indonesia when the UI was set to Basa Jawa, so the Javanese
screenshots showed Indonesian content under Javanese buttons. Live mode is unaffected (the model writes Javanese
itself). Brand names, part numbers and loanwords bengkels use as-is (busi, foot valve, seal tape, tubeless) stay.
api/tests/test_mock_javanese.py checks that every Indonesian demo string has an entry here.
"""
from __future__ import annotations

JV: dict[str, str] = {
    # ---------------------------------------------------------------- motor (Honda Beat, spark plug cap)
    "Honda Beat, area busi": "Honda Beat, bagean busi",
    "Cop busi": "Cop busi",
    "terlihat agak longgar": "katon rada longgar",
    "Kabel busi": "Kabel busi",
    "Filter udara": "Saringan hawa",
    "Cop busi tidak menempel rapat": "Cop busi ora nempel rapet",
    "Starter berputar tapi mesin tidak menyala: kemungkinan tidak ada percikan api.":
        "Starter muter nanging mesine ora urip: kemungkinan ora ana pletikan geni.",
    "Cop busi longgar": "Cop busi longgar",
    "Cop terlihat tidak rapat di foto": "Cop katon ora rapet ing foto",
    "Busi kotor / berkerak": "Busi reged / akeh kerake",
    "Susah hidup di pagi hari": "Angel urip yen esuk",
    "Filter udara tersumbat": "Saringan hawa buntu",
    "Ada bensin dan mesin bisa panas; kerjakan saat mesin dingin, jauh dari api.":
        "Ana bensin lan mesin bisa panas; garapen yen mesin wis adhem, adoh saka geni.",
    "Kunci busi 16 mm": "Kunci busi 16 mm",
    "Amplas halus / sikat kawat": "Amplas alus / sikat kawat",
    "Busi NGK CPR8EA-9 (cadangan)": "Busi NGK CPR8EA-9 (serep)",
    "Mesin mati dan sudah dingin (15 menit)": "Mesin mati lan wis adhem (15 menit)",
    "Jauh dari api dan rokok": "Adoh saka geni lan rokok",
    "Apakah tercium bau bensin saat distarter?": "Apa ana ambu bensin nalika distarter?",
    "Mesin hidup dan stasioner stabil.": "Mesin urip lan langsame ajeg.",
    "Bawa ke bengkel bila tercium bau bensin kuat.": "Gawanen menyang bengkel yen ambu bensine banter.",
    "Matikan kunci kontak dan tunggu mesin dingin 10 menit.": "Pateni kunci kontak lan enteni mesine adhem 10 menit.",
    "Kunci kontak di posisi OFF.": "Kunci kontak ing posisi OFF.",
    "Buka penutup samping lalu temukan cop busi (bagian yang ditandai nomor 1).":
        "Bukak tutup samping banjur golekana cop busi (perangan sing ditandhani nomer 1).",
    "Cop busi terlihat jelas di foto.": "Cop busi katon cetha ing foto.",
    "Tekan cop busi lurus ke dalam sampai terasa bunyi klik.": "Penet cop busi lurus mlebu nganti krasa muni klik.",
    "Cop busi menempel rapat tanpa celah.": "Cop busi nempel rapet tanpa sela.",
    "Pasang penutup, starter sambil tarik rem.": "Pasang tutupe, starter karo narik rem.",
    "Mesin menyala.": "Mesine urip.",
    "Mesin hidup dalam 3 kali starter.": "Mesin urip sajrone 3 kali starter.",
    "Bawa ke bengkel bila busi basah bensin atau tetap mati.": "Gawanen menyang bengkel yen busine teles bensin utawa tetep mati.",
    "Pastikan mesin mati dan dingin, lalu cabut cop busi.": "Priksa mesine mati lan adhem, banjur copot cop busi.",
    "Cop busi terlepas, busi terlihat.": "Cop busi wis copot, busine katon.",
    "Buka busi dengan kunci busi 16 mm, putar berlawanan jarum jam.": "Bukak busi nganggo kunci busi 16 mm, puteren mbalik arah jarum jam.",
    "Busi sudah di tangan, ujungnya terlihat.": "Busi wis ing tangan, pucuke katon.",
    "Bersihkan kerak di ujung busi dengan amplas halus sampai logamnya terlihat.":
        "Resiki kerak ing pucuk busi nganggo amplas alus nganti logame katon.",
    "Ujung busi bersih, tidak hitam pekat.": "Pucuk busi resik, ora ireng pekat.",
    "Pasang busi dengan tangan dulu, kencangkan 1/4 putaran, lalu pasang cop sampai bunyi klik.":
        "Pasang busi nganggo tangan dhisik, kencengna 1/4 puteran, banjur pasang cop nganti muni klik.",
    # ---------------------------------------------------------------- water pump (Shimizu, lost prime / foot valve)
    "Pompa air sumur dangkal (Shimizu)": "Pompa banyu sumur cethek (Shimizu)",
    "Baut pancingan": "Baut pancingan",
    "Pipa hisap": "Pipa sedhot",
    "sambungan agak basah": "sambungane rada teles",
    "Steker pompa": "Steker pompa",
    "Motor berputar tapi pipa keluar kering": "Motore muter nanging pipa metune garing",
    "Pompa menyala dan berputar, tapi air tidak keluar: pompa kehilangan pancingan.":
        "Pompa urip lan muter, nanging banyune ora metu: pancingane pompa ilang.",
    "Pompa kehilangan air pancingan": "Banyu pancingan pompa ilang",
    "Motor berputar, pipa keluar kering": "Motore muter, pipa metune garing",
    "Foot valve (klep kaki) tersumbat atau bocor": "Foot valve (klep sikil) buntu utawa bocor",
    "Pancingan cepat habis": "Pancingane cepet entek",
    "Sambungan pipa hisap bocor udara": "Sambungan pipa sedhot bocor hawa",
    "Sambungan terlihat basah": "Sambungane katon teles",
    "Pompa listrik 220V dekat air: selalu cabut steker dulu dan kerjakan dengan tangan kering.":
        "Pompa listrik 220V cedhak banyu: copot steker dhisik lan garapen nganggo tangan garing.",
    "Kunci ring 17 mm": "Kunci ring 17 mm",
    "Ember atau gayung": "Ember utawa gayung",
    "Foot valve 1\" (cadangan)": "Foot valve 1\" (serep)",
    "Steker pompa sudah dicabut": "Steker pompa wis dicopot",
    "Tangan dan lantai kering": "Tangan lan jogan garing",
    "Kran hisap dan keluar sudah ditutup": "Kran sedhot lan kran metu wis ditutup",
    "Air mengalir deras dalam 1 menit.": "Banyu mili deres sajrone 1 menit.",
    "Bila pancingan cepat habis lagi, cek foot valve; bila motor panas atau berbau hangus, panggil teknisi pompa.":
        "Yen pancingane cepet entek maneh, priksa foot valve; yen motore panas utawa ambu gosong, celuk teknisi pompa.",
    "Cabut steker pompa dari stop kontak dan pastikan tangan kering.": "Copot steker pompa saka stop kontak lan priksa tanganmu garing.",
    "Steker tercabut, pompa diam.": "Steker wis copot, pompa meneng.",
    "Buka baut pancingan di atas pompa dengan kunci ring 17 mm, putar berlawanan jarum jam.":
        "Bukak baut pancingan ing dhuwur pompa nganggo kunci ring 17 mm, puteren mbalik arah jarum jam.",
    "Lubang pancingan di atas pompa terbuka.": "Bolongan pancingan ing dhuwur pompa wis kebukak.",
    "Tuang air bersih pelan-pelan ke lubang pancingan sampai penuh dan meluap.":
        "Esokna banyu resik alon-alon menyang bolongan pancingan nganti kebak lan luber.",
    "Air terlihat penuh sampai bibir lubang.": "Banyune katon kebak nganti lambe bolongan.",
    "Lilit baut dengan seal tape, pasang lagi sampai kencang, colok steker, lalu buka kran.":
        "Lilit baut nganggo seal tape, pasang maneh nganti kenceng, colok steker, banjur bukak kran.",
    "Air keluar deras dari kran.": "Banyu metu deres saka kran.",
    "Air mengalir deras dalam 1 menit dan pancingan tidak habis lagi.": "Banyu mili deres sajrone 1 menit lan pancingane ora entek maneh.",
    "Bila motor mendengung tapi tidak berputar, panas, atau berbau hangus, panggil teknisi pompa.":
        "Yen motore mung ngguweng ora muter, panas, utawa ambu gosong, celuk teknisi pompa.",
    "Angkat pipa hisap dari sumur sampai foot valve di ujungnya terlihat.": "Angkaten pipa sedhot saka sumur nganti foot valve ing pucuke katon.",
    "Foot valve di ujung pipa terlihat jelas.": "Foot valve ing pucuk pipa katon cetha.",
    "Bersihkan saringan foot valve dari lumpur dan daun, lalu tekan kleppnya: harus membuka dan menutup lancar.":
        "Resiki saringan foot valve saka lendhut lan godhong, banjur penet klepe: kudu mbukak lan nutup lancar.",
    "Saringan bersih dan klep bergerak lancar.": "Saringan resik lan klepe obah lancar.",
    "Turunkan lagi pipanya, isi air pancingan sampai meluap, pasang baut, lalu colok steker.":
        "Mudhunna maneh pipane, isenana banyu pancingan nganti luber, pasang baut, banjur colok steker.",
    # ---------------------------------------------------------------- faucet (worn washer / valve seat)
    "Kran air wastafel dapur": "Kran banyu wastafel pawon",
    "Tuas kran": "Gagang kran",
    "Mulut kran": "Cangkem kran",
    "basah, menetes": "teles, netes",
    "Kran stop": "Kran stop",
    "Tetesan air di ujung mulut kran": "Tetesan banyu ing pucuk cangkem kran",
    "Kran menetes dari mulut kran saat ditutup.": "Kran netes saka cangkeme senajan wis ditutup.",
    "Seal karet di dalam kran aus": "Seal karet ing jero kran wis aus",
    "Tetes dari mulut kran saat tertutup": "Netes saka cangkem kran nalika ketutup",
    "Dudukan katup tergores": "Lungguhan klep kegores",
    "Air dan bagian kecil; risiko rendah.": "Banyu lan perangan cilik; risikone cilik.",
    "Kunci inggris": "Kunci inggris",
    "Obeng plus": "Obeng plus",
    "Seal karet kran 1/2\"": "Seal karet kran 1/2\"",
    "Kran stop di bawah wastafel sudah ditutup": "Kran stop ing ngisor wastafel wis ditutup",
    "Tidak ada tetesan selama 2 menit.": "Ora ana tetesan sajrone 2 menit.",
    "Berhenti bila badan kran retak atau pipa di tembok ikut bocor.": "Mandhega yen awak kran retak utawa pipa ing tembok melu bocor.",
    "Putar kran stop di bawah wastafel searah jarum jam sampai mentok.": "Puteren kran stop ing ngisor wastafel searah jarum jam nganti mentok.",
    "Air tidak keluar saat kran dibuka.": "Banyu ora metu nalika kran dibukak.",
    "Congkel tutup tuas, buka sekrupnya, lalu angkat tuas kran.": "Cungkili tutup gagang, bukak sekrupe, banjur angkaten gagang kran.",
    "Batang kran (spindle) terlihat.": "Gagang jero kran (spindle) katon.",
    "Buka kepala kran dengan kunci inggris berlapis kain, ganti seal karetnya.":
        "Bukak sirah kran nganggo kunci inggris sing dilapisi kain, ganti seal karete.",
    "Seal baru duduk rata di ujung kepala kran.": "Seal anyar lungguh rata ing pucuk sirah kran.",
    "Pasang kembali, buka kran stop pelan-pelan, lalu tutup kran wastafel.": "Pasang maneh, bukak kran stop alon-alon, banjur tutup kran wastafel.",
    "Mulut kran kering, tidak ada tetesan.": "Cangkem kran garing, ora ana tetesan.",
    "Bila masih menetes, ganti kran utuh (sekitar Rp60.000) atau panggil tukang ledeng.":
        "Yen isih netes, ganti kran sakwutuhe (kira-kira Rp60.000) utawa celuk tukang ledheng.",
    "Tutup lagi kran stop di bawah wastafel.": "Tutupen maneh kran stop ing ngisor wastafel.",
    "Lepas tuas dan kepala kran seperti sebelumnya.": "Copoten gagang lan sirah kran kaya mau.",
    "Lubang dudukan katup terlihat.": "Bolongan lungguhan klep katon.",
    "Haluskan dudukan katup dengan alat pengasah dudukan (reseating tool), putar 3-4 kali.":
        "Alusna lungguhan klep nganggo piranti asah lungguhan (reseating tool), puteren 3-4 kali.",
    "Permukaan dudukan rata dan mengkilap.": "Lumahe lungguhan rata lan mengkilap.",
    "Pasang kembali dengan seal baru, buka kran stop, lalu tutup kran.": "Pasang maneh nganggo seal anyar, bukak kran stop, banjur tutup kran.",
    "Mulut kran kering.": "Cangkem kran garing.",
    # ---------------------------------------------------------------- rice cooker (red stop)
    "Rice cooker (magic com)": "Rice cooker (magic com)",
    "Tombol cook": "Tombol cook",
    "Kabel power": "Kabel listrik",
    "Lampu indikator mati": "Lampu indikator mati",
    "Rice cooker tidak memanas; lampu indikator mati.": "Rice cooker ora panas; lampu indikatore mati.",
    "Sekring termal di dalam putus": "Sekring termal ing jero pedhot",
    "Kabel power rusak": "Kabel listrik rusak",
    "Perlu membuka bagian dalam alat 220V.": "Kudu mbukak jeroan piranti 220V.",
    # ---------------------------------------------------------------- flat scooter tyre (nail / valve stem)
    "Ban belakang motor skutik (tubeless)": "Ban mburi motor matic (tubeless)",
    "Tapak ban": "Tapak ban",
    "ada benda logam menancap": "ana barang wesi nancep",
    "Pentil (ventil)": "Pentil (ventil)",
    "Pelek": "Pelek",
    "Ban kempes dan ada paku di tapak": "Ban kempes lan ana paku ing tapake",
    "Ban belakang kempes pelan-pelan: ada paku menancap di tapak ban tubeless.":
        "Ban mburi kempes alon-alon: ana paku nancep ing tapak ban tubeless.",
    "Paku menancap di tapak ban": "Paku nancep ing tapak ban",
    "Ada benda logam di tapak ban": "Ana barang wesi ing tapak ban",
    "Pentil (ventil) bocor": "Pentil (ventil) bocor",
    "Kempes pelan tanpa luka terlihat": "Kempes alon tanpa tatu sing katon",
    "Pelek penyok atau bibir ban tidak rapat": "Pelek penyok utawa lambe ban ora rapet",
    "Motor harus stabil di standar tengah dan jangan ditambal di jalan ramai; tambalan cacing hanya sementara.":
        "Motor kudu ajeg ing standar tengah lan aja ditambal ing dalan rame; tambalan cacing mung sementara.",
    "Set tambal ban tubeless (cacing)": "Set tambal ban tubeless (cacing)",
    "Tang": "Tang",
    "Pompa tangan atau pompa angin": "Pompa tangan utawa pompa angin",
    "Cacing tambal cadangan": "Cacing tambal serep",
    "Air sabun dalam botol semprot": "Banyu sabun ing botol semprot",
    "Motor mati dan di tempat datar": "Motor mati lan ing panggonan rata",
    "Jauh dari jalan ramai": "Adoh saka dalan rame",
    "Ban tetap keras setelah 30 menit dan air sabun tidak berbusa.": "Ban tetep atos sawise 30 menit lan banyu sabun ora umpluk.",
    "Tambalan cacing bersifat sementara. Bawa ke tukang tambal ban bila lukanya di dinding samping ban atau lebih dari 6 mm.":
        "Tambalan cacing mung sementara. Gawanen menyang tukang tambal ban yen tatune ing tembok samping ban utawa luwih saka 6 mm.",
    "Naikkan motor ke standar tengah di tempat datar dan jauh dari jalan ramai.":
        "Munggahna motor ing standar tengah ing panggonan rata lan adoh saka dalan rame.",
    "Motor berdiri stabil di standar tengah.": "Motor ngadeg ajeg ing standar tengah.",
    "Putar roda pelan sampai paku terlihat, lalu tarik paku lurus dengan tang.":
        "Puteren roda alon-alon nganti pakune katon, banjur tarik paku lurus nganggo tang.",
    "Paku sudah keluar dan lubangnya terlihat.": "Pakune wis metu lan bolongane katon.",
    "Lebarkan lubang dengan alat peraut dari set tambal, masukkan cacing ke jarum tusuk yang sudah diolesi lem.":
        "Ambakna bolongan nganggo piranti rautan saka set tambal, lebokna cacing menyang jarum tusuk sing wis diolesi lem.",
    "Cacing terpasang rapi di ujung jarum.": "Cacing wis kepasang rapi ing pucuk jarum.",
    "Tusuk jarum lurus ke lubang, tarik jarum cepat dan lurus, potong sisa cacing, lalu pompa ban sesuai angka di stiker motor.":
        "Tusukna jarum lurus menyang bolongan, tarik jarum cepet lan lurus, potong turahan cacing, banjur pompanen ban miturut angka ing stiker motor.",
    "Tidak ada gelembung saat disemprot air sabun.": "Ora ana umpluk nalika disemprot banyu sabun.",
    "Ban tetap keras setelah 30 menit.": "Ban tetep atos sawise 30 menit.",
    "Bila masih kempes, bawa ke tukang tambal ban untuk cek pelek dan bibir ban.":
        "Yen isih kempes, gawanen menyang tukang tambal ban kanggo mriksa pelek lan lambe ban.",
    "Semprot pentil dengan air sabun dan lihat apakah muncul gelembung.": "Semproten pentil nganggo banyu sabun lan delengen apa ana umpluk.",
    "Pentil basah berbusa dan terlihat jelas.": "Pentil teles umpluken lan katon cetha.",
    "Kencangkan inti pentil dengan alat pembuka pentil, putar searah jarum jam sampai kencang pas.":
        "Kencengna isi pentil nganggo piranti pambuka pentil, puteren searah jarum jam nganti kenceng pas.",
    "Gelembung berhenti keluar dari pentil.": "Umpluk wis ora metu saka pentil.",
    "Pompa ban sesuai angka di stiker motor, pasang tutup pentil, lalu cek lagi dengan air sabun.":
        "Pompanen ban miturut angka ing stiker motor, pasang tutup pentil, banjur priksa maneh nganggo banyu sabun.",
    "Tidak ada gelembung baru di pentil.": "Ora ana umpluk anyar ing pentil.",
    # ---------------------------------------------------------------- step check
    "Foto terlalu gelap, bagiannya tidak terlihat.": "Fotone kepetengen, perangane ora katon.",
    "Nyalakan senter HP dan foto lebih dekat ke bagian yang ditandai.": "Urubna senter HP lan foto luwih cedhak menyang perangan sing ditandhani.",
    "Foto kosong atau buram.": "Fotone kosong utawa burem.",
    "Arahkan kamera ke bagian yang ditandai dan tahan HP tetap diam.": "Arahna kamera menyang perangan sing ditandhani lan cekel HP aja obah.",
    "Terlihat sesuai dengan kondisi yang diharapkan.": "Katon cocog karo kahanan sing dikarepake.",
}


def jv(id_text: str) -> str:
    """The Javanese demo text for an Indonesian one (unchanged when there is no entry)."""
    return JV.get(id_text, id_text)
