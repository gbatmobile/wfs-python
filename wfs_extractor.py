# encoding: utf-8

version = "WFS0.4/5 Extractor 0.4"
copyright = \
'''
    \nThis program can identify and recover videos stored\n\
	in a WFS0.4/5 filesystem (common in chinese's DVR). \n\n\
    Under Windows, you can only open dd images. In Linux\n\
    you can access evidence disk or image using names in file system.\n\
    Be careful when using disk directly (this may not be a correct \n\
    forensic approach in many situations!!!). \n\n\
	WFS0.4 extractor is offered to you under MIT license by:\n\n\
          UNALDO Brito (unaldo.brito@gmail.com)\n\
          GALILEU Batista (galileu.batista@ifrn.edu.br)\n\n\
    You must retain the authors names in all\n\
    circunstances in which the program is used.\n\
    The authors have made their best to get a correct\n\
    operation, but no warranty implicit or explicit\n\
    is provided.
'''

import wx
import os, sys, platform
import time

def extract_bits(numb, position, tam):
    return (numb >> (position + 1 - tam)) & ((1 << tam) - 1)

def decodeTimeStamp(ts):
    return extract_bits(ts, 31, 6), extract_bits(ts, 25, 4), extract_bits(ts, 21, 5),\
           extract_bits(ts, 16, 5), extract_bits(ts, 11, 6), extract_bits(ts, 5, 6)

class Janela(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Janela, self).__init__(*args, **kwargs)
        self.SetSize(700,550)
        self.desc = 32  # tamanho do descritor
        self.primeira = []  # Lista para guardar as primeiras posições
        self.lista = []  # Lista para ser colocados os indices dos videos a serem baixados
        self.lista_principais = []  # Lista para guardar todos os descritores principais
        self.lista_meta = []  # Lista com os metadados para formar os nomes dos vídeos recuperados
        self.camera = 0
        self.imagem_carregada = False # Controla a exibição dos metadados

        self.gui()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def gui(self):
        self.CreateStatusBar()

        splitter = wx.SplitterWindow(self, style=wx.SP_NOSASH)
        self.painel = wx.Panel(splitter)
        self.painel1 = wx.Panel(splitter)
        splitter.SplitVertically(self.painel1, self.painel)
        splitter.SetSashGravity(0.27)

        # ToolBar
        self.tb = wx.ToolBar(self, wx.ID_ANY, style=wx.TB_TEXT)
        self.ToolBar = self.tb
        self.tb.AddTool(toolId=101, label="Open Image", bitmap=wx.Bitmap(self.resource_path("icons/open.png")))
        if os.name != 'nt':
            self.tb.AddTool(toolId=102, label="Open Disk", bitmap=wx.Bitmap(self.resource_path("icons/open.png")))
        self.tb.AddTool(toolId=103, label="Info", bitmap=wx.Bitmap(self.resource_path("icons/info.png")))
        self.tb.AddTool(toolId=104, label="Extract", bitmap=wx.Bitmap(self.resource_path("icons/extract.png")))
        self.tb.AddTool(toolId=105, label="Recover", bitmap=wx.Bitmap(self.resource_path("icons/recover.png")))
        self.tb.AddTool(toolId=106, label="Slack", bitmap=wx.Bitmap(self.resource_path("icons/slack.png")))
        self.tb.AddTool(toolId=107, label="About", bitmap=wx.Bitmap(self.resource_path("icons/info.png")))
        self.tb.AddTool(toolId=108, label="Exit", bitmap=wx.Bitmap(self.resource_path("icons/exit.png")))
        self.tb.Bind(wx.EVT_TOOL, self.toolBarEvent)
        self.tb.Realize()
        self.SetTitle(version)
        self.Centre()

        self.Show(True)
        time.sleep(1)
        self.dlg_about()

    def toolBarEvent(self, e):
        if e.GetId() == 101:
            self.abrir_dialogo()
        if e.GetId() == 102:
            self.abrir_comboDisk()
        elif e.GetId() == 103:
            self.dlg_metadados()
        elif e.GetId() == 104:
            self.recupera_videos()
        elif e.GetId() == 105:
            self.recupera_apagados()
        elif e.GetId() == 106:
            self.recupera_slack()
        elif e.GetId() == 107:
            self.dlg_about()
        elif e.GetId() == 108:
            self.sair()

    def decodeBlockStructure(self, descBytes): # Retorna um dicionário com os atributos de cada fragmento
        b_ano, b_mes, b_dia, b_hora, b_min, b_seg = decodeTimeStamp(int.from_bytes(descBytes[12:16], byteorder='little'))
        e_ano, e_mes, e_dia, e_hora, e_min, e_seg = decodeTimeStamp(int.from_bytes(descBytes[16:21], byteorder='little'))
        dic = {
            'b_ano'        : b_ano,'b_mes': b_mes,'b_dia': b_dia,'b_hora': b_hora,'b_min': b_min,'b_seg': b_seg,
            'e_ano'        : e_ano,'e_mes': e_mes,'e_dia': e_dia,'e_hora': e_hora,'e_min': e_min,'e_seg': e_seg,
            'attrib'       : int.from_bytes(descBytes[1:2], byteorder='little'),
            'totBlocks'    : int.from_bytes(descBytes[2:4], byteorder='little') + 1,
            'prevBlock'    : int.from_bytes(descBytes[4:8], byteorder='little'),
            'nextBlock'    : int.from_bytes(descBytes[8:12], byteorder='little'),
            'begTimeStamp' : "20{0:02d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(b_ano, b_mes, b_dia, b_hora, b_min, b_seg),
            'endTimeStamp' : "20{0:02d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(e_ano, e_mes, e_dia, e_hora, e_min, e_seg),
            'totalSize'    : ((int.from_bytes(descBytes[2:4], byteorder='little')) * self.fragmento + int.from_bytes(descBytes[22:24], byteorder='little') * self.bloco) / 1048576,
            'beginBlock'   : int.from_bytes(descBytes[24:28], byteorder='little'),
            'camera'       : (int.from_bytes(descBytes[31:32], byteorder='little') + 2) // 4,
            'tamUltFrag'   : int.from_bytes(descBytes[22:24], byteorder='little') * self.bloco
        }
        # print (f"beginblock: {dic['beginBlock']} -> {dic['begTimeStamp']} cam{dic['camera']}")

        return dic

    def abrir_dialogo(self):
        #wildcard = "Text Files (*.img)|*.img"
        self.dlg = wx.FileDialog(self, "Choose a file...", os.getcwd(), "")
        if self.dlg.ShowModal() == wx.ID_OK:
            self.carrega_imagem(self.dlg.GetPath())

    def abrir_comboDisk(self):
        DiskSelection(self)

    def carrega_imagem(self, path):

        self.disco = open(path, "rb")

        # Verifica e confirma se trata-se de um Sistema de Arquivos WFS0.4 e libera as funções do programa
        if self.disco.read(6) in [b'WFS0.4', b'WFS0.5']:
            self.camera = 0

            self.disco.seek(0x3010)
            b_ano, b_mes, b_dia, b_hora, b_min, b_seg = decodeTimeStamp(int.from_bytes(self.disco.read(4), byteorder='little'))
            self.firstDate = "20{0:02d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(b_ano, b_mes, b_dia, b_hora, b_min, b_seg)
            print ("First fragmento: ",  self.firstDate)
            e_ano, e_mes, e_dia, e_hora, e_min, e_seg = decodeTimeStamp(int.from_bytes(self.disco.read(4), byteorder='little'))

            self.disco.seek(0x302c)
            self.bloco = int.from_bytes(self.disco.read(4), byteorder='little')  # Tamanho do bloco
            print ("Block Size ",  self.bloco)
            self.fragmento = int.from_bytes(self.disco.read(4),byteorder='little') * self.bloco  # Tamanho do fragmento de video
            print ("Fragment size ",  self.fragmento)
            self.disco.seek(0x3038)
            self.qtd_reservados = (int.from_bytes(self.disco.read(4), byteorder='little'))
            self.disco.seek(0x3044)
            self.inicio_descritores = (int.from_bytes(self.disco.read(4), byteorder='little')) * self.bloco
            print ("Start of descriptors: ",  self.inicio_descritores)
            self.inicio_videos = (int.from_bytes(self.disco.read(4), byteorder='little')) * self.bloco
            print ("Start of videos: ",  self.inicio_videos)
            self.qtd_frag = (int.from_bytes(self.disco.read(4), byteorder='little'))
            print ("Number of fragments: ",  self.qtd_frag)
            self.desc_principais()
            self.listar_datas()
            self.listar_videos()
        else:
            wx.MessageBox("This is not a WFS0.[45] filesystem!!!", version, style=wx.OK | wx.ICON_INFORMATION)

        self.imagem_carregada = True

    def dlg_about(self):
        wx.MessageBox(copyright, "About", style=wx.OK)


    # Exibir dialog com os metadados quando o botão info for pressionado
    def dlg_metadados(self):

        if self.imagem_carregada:
            self.disco.seek(3014)

            mensagem = "METADATA for the WFS0.4 filesystem\n\n" \
                       "Number of fragments: {0}\n" \
                       "Number of videos: {1}\n" \
                       "Standard fragment size: {2}\n" \
                       "Number of reserved fragment: {3}\n" \
                       "Number of free fragments: {4}\n" \
                       "Reserved area before data area: {5:.0f} MB\n" \
                       "First vídeo timestamp (in superblock): {6}\n" \
                       "Last vídeo timestamp (in video descriptors): {7}\n".format(self.qtd_frag, len(self.lista_principais), self.fragmento,
                                                                       self.qtd_reservados,
                                                                       len(self.freeFrags),
                                                                       self.qtd_reservados*self.fragmento/1048576,
                                                                       self.firstDate,
                                                                       self.lastDate)
            wx.MessageBox(mensagem, "WFS0.4 Metadata", style=wx.OK)
        else:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)

    # Separar todos os descritores principais
    def desc_principais(self):
        self.SetStatusText("Loading...")
        self.lista_principais = []
        self.freeFrags = []
        self.disco.seek(self.inicio_descritores)
        allAtribs = {}

        self.lastDate = "00"
        for i in range(self.qtd_frag):
            descritor = self.disco.read(self.desc)
            dic = self.decodeBlockStructure(descritor)
            allAtribs[dic['attrib']] = allAtribs.get(dic['attrib'],0)+1
            if (dic['attrib'] in [2, 3]) and (dic['begTimeStamp'] != dic['endTimeStamp']):
                self.lista_principais.append(descritor)
                self.lastDate = max (self.lastDate, dic['endTimeStamp'])
            elif dic['attrib'] == 0:
                self.freeFrags.append(i)
        self.separados = self.lista_principais
        self.SetStatusText("Loaded!")

    # Listar as datas e as câmeras em ListBoxes
    def listar_datas(self):
        datas = ["All"]
        cameras = ["All"]

        for descritor in self.lista_principais:
            dic = self.decodeBlockStructure(descritor)
            data = "{0:02d} - {1:02d} - 20{2}".format(dic['b_dia'], dic['b_mes'], dic['b_ano'])

            if data not in datas:
                datas.append(data)

            if dic['camera'] < 10:
                cam = "0{}".format(str(dic['camera']))
            else:
                cam = str(dic['camera'])

            if cam not in cameras:
                cameras.append(cam)

        # textos para as ListBox de datas e câmeras
        wx.StaticText(self.painel1, label="Date", pos=(40, 10))
        wx.StaticText(self.painel1, label="Camera", pos=(125, 10))

        # ListBoxes para selecionar datas e câmeras
        self.lb_datas = wx.ListBox(self.painel1, pos=(10, 30), size=(100, 370), choices=datas, style=wx.LB_SINGLE)
        self.lb_datas.SetSelection(0)
        self.lb_datas.SetFirstItem(0)
        self.Bind(wx.EVT_LISTBOX, self.separa_descritores, self.lb_datas)

        self.lb_cam = wx.ListBox(self.painel1, pos=(120, 30), size=(70, 370), choices=cameras, style=wx.LB_SINGLE)
        self.lb_cam.SetSelection(0)
        self.lb_cam.SetFirstItem(0)
        self.Bind(wx.EVT_LISTBOX, self.sel_camera, self.lb_cam)

    # Evento de seleção da cÂmera
    def sel_camera(self, event):
        if self.lb_cam.GetStringSelection() == "All":
            self.camera = 0
        else:
            self.camera = self.lb_cam.GetStringSelection()
        self.listar_videos()
        #print(self.camera)

    def separa_descritores(self, event):
        self.separados = []
        if self.lb_datas.GetStringSelection() == "All":
            self.separados = self.lista_principais

        else:
            for descritor in self.lista_principais:
                dic = self.decodeBlockStructure(descritor)
                data = "{0:02d} - {1:02d} - 20{2}".format(dic['b_dia'], dic['b_mes'], dic['b_ano'])
                if data == self.lb_datas.GetStringSelection():
                    self.separados.append(descritor)

        #print(len(self.separados))
        self.listar_videos()

    # lista os vídeos na tela, separa as posições dos descritores principais e cria lista com metadados
    def listar_videos(self):
        larg = 0 # Variável usada para corrigir a largura do ListCtrl

        self.SetStatusText("Loading...")

        # Apagar lista de vídeos anterior
        self.apagar()

        # Cria área para os vídeos
        self.area_videos = wx.ListCtrl(self.painel, -1, pos=(10, 0), size=(480, 400), style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.cabecalho = ["DATA", "BEGIN", "END", "CAMERA", "SIZE"]
        self.area_videos.InsertColumn(0, "ID", wx.LIST_FORMAT_CENTER, width=wx.LIST_AUTOSIZE)
        larg = self.area_videos.GetColumnWidth(0)
        self.area_videos.Bind(wx.EVT_LIST_ITEM_SELECTED, self.monta_lista)
        self.area_videos.SetBackgroundColour(wx.WHITE)
        for i in range(len(self.cabecalho)):
            self.area_videos.InsertColumn(i+1, self.cabecalho[i], wx.LIST_FORMAT_CENTER, width=wx.LIST_AUTOSIZE)
            larg += self.area_videos.GetColumnWidth(i+1)

        self.area_videos.SetSize(larg+10, 400)

        id = 0
        self.disco.seek(self.inicio_descritores)
        self.primeira = []
        self.lista = []
        self.lista_meta = []
        sep = []
        if self.camera != 0:
            for desc in self.separados:
                dic = self.decodeBlockStructure(desc)
                if dic['camera'] == int(self.camera):
                    sep.append(desc)
            descritores = sep
        else:
            descritores = self.separados

        for descritor in descritores:
            dic = self.decodeBlockStructure(descritor)
            self.primeira.append(dic['beginBlock'] * self.desc + self.inicio_descritores)

            data = "{0:02d}-{1:02d}-20{2}".format(dic['b_dia'],dic['b_mes'],dic['b_ano'])
            inicio = "{0:02d}:{1:02d}:{2:02d}".format(dic['b_hora'],dic['b_min'],dic['b_seg'])
            fim = "{0:02d}:{1:02d}:{2:02d}".format(dic['e_hora'], dic['e_min'], dic['e_seg'])
            cam = "{0:02d}".format(dic['camera'])
            tam = "{0:.2f} MB".format(dic['totalSize'])

            self.area_videos.InsertItem(id, str(id))
            self.area_videos.SetItem(id, 1, data)
            self.area_videos.SetItem(id, 2, inicio)
            self.area_videos.SetItem(id, 3, fim)
            self.area_videos.SetItem(id, 4, cam)
            self.area_videos.SetItem(id, 5, tam)

            self.lista_meta.append("{0}-{1}-{2}-[{3}]".format(data, inicio, fim, cam))
            id += 1
            self.SetStatusText("Listing Videos... {0:.2f}%".format((id/len(self.separados)) * 100))

        self.SetStatusText("Done!!!!!!!!!")

    # Separa as posições dos descritores secundários para cada descritor principal
    def guarda_pos(self, inicio):
        self.disco.seek(inicio)
        descritor = self.disco.read(self.desc)
        dic = self.decodeBlockStructure(descritor)
        ultimo = dic['tamUltFrag']
        pedacos = [dic['beginBlock']]
        nBlocks = dic['totBlocks']

        for i in range(1, nBlocks):
                pedacos.append(dic['nextBlock'])
                self.disco.seek(dic['nextBlock'] * self.desc + self.inicio_descritores)
                descritor = self.disco.read(self.desc)
                dic = self.decodeBlockStructure(descritor)

        return pedacos, ultimo

    def canonize_path(self, path):
        if platform.system() == 'Windows':
            try:
                os.mkdir(os.getcwd()+"\\"+path)
                caminho = os.getcwd()+"\\"+path+"\\"
            except FileExistsError:
                caminho = os.getcwd()+"/"+path+"\\"
        else:
            try:
                os.mkdir(os.getcwd()+"/"+path)
                caminho = os.getcwd()+"/"+path+"/"
            except FileExistsError:
                caminho = os.getcwd()+"/"+path+"/"
        return caminho

    def recupera_videos(self):
        if not self.imagem_carregada:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)
            return

        if len(self.lista) > 0:
            caminho = self.canonize_path("WFS0.4_Extractor_Videos")

            nVideos = 0
            for l in range(len(self.lista)):
                pedacos, ultimo = self.guarda_pos(self.primeira[self.lista[l]])

                nome = f"Video-{pedacos[0]:06d}-{self.lista_meta[self.lista[l]]}.h264".replace(":","-")
                self.SetStatusText("Saving vídeo {0} in folder {1}".format(nome, caminho))
                arq = open(caminho+nome, "wb")

                inicio_real = self.inicio_videos
                for i in range(len(pedacos) - 1):
                    desloc = inicio_real + pedacos[i] * self.fragmento
                    self.disco.seek(desloc)
                    frag = self.disco.read(self.fragmento)
                    arq.write(frag)

                desloc = inicio_real + pedacos[-1] * self.fragmento
                self.disco.seek(desloc)
                frag = self.disco.read(ultimo)
                arq.write(frag)
                arq.close()
                nVideos += 1

            wx.MessageBox("{0} Video(s) sucessfully saved in folder {1}".format(nVideos, caminho), style=wx.OK)

            self.SetStatusText("Done!!")
        else:
            wx.MessageBox("Choose one or more videos", version, style=wx.OK | wx.ICON_INFORMATION)

    def recupera_apagados(self):
        if self.imagem_carregada:
            wx.MessageBox("This is a experimental feature. It will work in ONE camera system only!!",
                            version, style=wx.OK | wx.ICON_INFORMATION)

            caminho = self.canonize_path("WFS0.4_Extractor_Recovered")
            fragHeader = b'\x00\x00\x00\x00'

            nVideos = 0
            arq = None
            for i in self.freeFrags:
                desloc = self.inicio_videos + i * self.fragmento
                self.disco.seek(desloc)
                frag = self.disco.read(self.fragmento)

                if frag[0:4] == h264Signature:
                    if arq:
                        nVideos += 1
                        arq.close()

                    nome = f"Frag-{i:06d}.h264"
                    arq = open(caminho+nome, "wb")
                    arq.write(frag)
                    self.SetStatusText("Saving vídeo {0} in folder {1}".format(nome, caminho))
                elif arq:
                    arq.write(frag)

            if arq:
                nVideos += 1
                arq.close()

            wx.MessageBox("{0} Video(s) sucessfully saved in folder {1}".format(nVideos, caminho), style=wx.OK)

            self.SetStatusText("Done!!")
        else:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)

    def recupera_slack(self):
        if not self.imagem_carregada:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)
            return

        if len(self.lista) > 0:
            caminho = self.canonize_path("WFS0.4_Extractor_Slack")

            nVideos = 0
            for l in range(len(self.lista)):
                pedacos, ultimo = self.guarda_pos(self.primeira[self.lista[l]])

                desloc = self.inicio_videos + pedacos[-1] * self.fragmento + ultimo
                self.disco.seek(desloc)
                frag = self.disco.read(self.fragmento - ultimo)

                startFrame = frag.find(h264Signature)
                if startFrame != -1:
                    nome = f"Slack-{pedacos[0]:06d}-{pedacos[-1]:06d}.h264"
                    self.SetStatusText("Saving vídeo {0} in folder {1}".format(nome, caminho))
                    arq = open(caminho+nome, "wb")
                    arq.write(frag[startFrame:])
                    arq.close()
                    nVideos += 1
                else:
                    print ("Vídeo not found on slack "+str(pedacos[-1]))

            wx.MessageBox("{0} Video(s) sucessfully saved in folder {1}".format(nVideos, caminho), style=wx.OK)

            self.SetStatusText("Done!!")
        else:
            wx.MessageBox("Choose one or more videos", version, style=wx.OK | wx.ICON_INFORMATION)

    # função para montar a lista com os vídeos a serem baixados
    def monta_lista(self, event):
        id = event.GetIndex()
        if id in self.lista:
            self.lista.remove(id)
            self.area_videos.SetItemBackgroundColour(event.GetIndex(), wx.WHITE)
        else:
            self.lista.append(id)
            self.area_videos.SetItemBackgroundColour(event.GetIndex(), wx.GREEN)

        #print(self.lista)
        #print(self.lista_meta)

    # Apaga todas as informações na lista de vídeos
    def apagar(self):
        for child in self.painel.GetChildren():
            child.Destroy()

    def sair(self):
        self.Close()

class DiskSelection(wx.Frame):
    def __init__(self, parent):
        super(DiskSelection, self).__init__(parent, title = "Select Physical Drive",size = (300,100))
        self.Janela = parent
        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)
        cblbl = wx.StaticText(panel,label = "Disks:",style = wx.ALIGN_CENTRE)
        box.Add(cblbl,0,wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL,1)
        disks = []

        for d in range(25):
            diskName = f"\\\\.\\PhysicalDrive{d}"
            try:
                fd = open(diskName, 'rb')
                signature = fd.read(6)
                if signature in [b'WFS0.4', b'WFS0.5']:
                    diskName += '( '+signature.decode()+' )'
                disks.append(diskName)
                fd.close()
            except:
                None
        if (len(disks) > 0):
            self.combo = wx.ComboBox(panel,choices = disks)
            box.Add(self.combo,1,wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL,1)
            self.combo.SetSelection(0)
            self.combo.Bind(wx.EVT_COMBOBOX, self.onSelect)
            lbl2 = wx.StaticText(panel,label = "Note WFS0.4/5 disks highlighted!!!",style = wx.ALIGN_CENTRE)
            box.Add(lbl2,0,wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL,2)

            panel.SetSizer(box)
            self.Centre()
            self.Show(True)
        else:
            wx.MessageBox("No disks found. Make sure you \nare running as administrator")


    def onSelect(self, event):
        self.Close()
        self.Janela.carrega_imagem(self.combo.GetValue())

h264Signature = b'\x00\x00\x01\xFC'
if __name__ == '__main__':
    app = wx.App()
    main = Janela(None)
    app.MainLoop()
