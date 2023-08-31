# encoding: utf-8

version = "WFS0.4/5 Extractor 0.3"
copyright = \
'''
    \nThis program can identify and recover videos stored\n\
	in a WFS0.4/5 filesystem (common in chinese's DVR). \n\n\
    When running under Windows, you must run as administrator \n\
    and use 'Open Disk' or 'Open Image' to get data source. In Linux\n\
    you can access evidence disk or image using names in file system.\n\
    Be careful when using disk directly (this may not be a correct \n\
    forensic approach in many situations!!!). \n\n\
	WFS0.4 extractor is offered to you under GPL license by:\n\n\
          UNALDO Brito (unaldo.brito@gmail.com)\n\
          GALILEU Batista (galileu.batista@ifrn.edu.br)\n\n\
    You must retain the authors names in all\n\
    circunstances in which the program is used.\n\
    The authors have made their best to get a correct\n\
    operation, but no warranty implicit or explicit\n\
    is provided.
'''

# Howto create a Virtualbox to access windows physical disk on Linux Box
# VBoxManage internalcommands createrawvmdk -filename
#            "C:\tmp\wfs.vmdk" -rawdisk \\.\PhysicalDrive2

import wx
import os
import platform
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
        self.tb.AddTool(toolId=101, label="Open Image", bitmap=wx.Bitmap("icons/abrir.png"))
        if os.name == 'nt':
            self.tb.AddTool(toolId=110, label="Open Disk", bitmap=wx.Bitmap("icons/abrir.png"))
        self.tb.AddTool(toolId=102, label="Info", bitmap=wx.Bitmap("icons/info.png"))
        self.tb.AddTool(toolId=103, label="Extract", bitmap=wx.Bitmap("icons/baixar.png"))
        self.tb.AddTool(toolId=104, label="About", bitmap=wx.Bitmap("icons/info.png"))
        self.tb.AddTool(toolId=105, label="Exit", bitmap=wx.Bitmap("icons/sair.png"))
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
        if e.GetId() == 110:
            self.abrir_comboDisk()
        elif e.GetId() == 102:
            self.dlg_metadados()
        elif e.GetId() == 103:
            self.recupera_videos()
        elif e.GetId() == 104:
            self.dlg_about()
        elif e.GetId() == 105:
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
        print (f"beginblock: {dic['beginBlock']} -> {dic['begTimeStamp']} cam{dic['camera']}")

        return dic

    def abrir_dialogo(self):
        #wildcard = "Text Files (*.img)|*.img"
        self.dlg = wx.FileDialog(self, "Escolha um arquivo", os.getcwd(), "")
        if self.dlg.ShowModal() == wx.ID_OK:
            self.carrega_imagem(self.dlg.GetPath())

    def abrir_comboDisk(self):
        DiskSelection(self)

    def carrega_imagem(self, path):

        self.disco = open(path, "rb")
#        self.disco = open(os.open("\\\\.\\PhysicalDrive2", os.O_RDONLY|os.O_BINARY), "rb")

        # Verifica e confirma se trata-se de um Sistema de Arquivos WFS0.4 e libera as funções do programa
        if self.disco.read(6) in [b'WFS0.4', b'WFS0.5']:
            self.camera = 0
            self.disco.seek(0x302c)
            self.bloco = int.from_bytes(self.disco.read(4), byteorder='little')  # Tamanho do bloco
            self.fragmento = int.from_bytes(self.disco.read(4),byteorder='little') * self.bloco  # Tamanho do fragmento de video
            self.disco.seek(0x3038)
            self.qtd_reservados = (int.from_bytes(self.disco.read(4), byteorder='little'))
            self.disco.seek(0x3044)
            self.inicio_descritores = (int.from_bytes(self.disco.read(4), byteorder='little')) * self.bloco
            self.inicio_videos = (int.from_bytes(self.disco.read(4), byteorder='little')) * self.bloco
            self.qtd_frag = (int.from_bytes(self.disco.read(4), byteorder='little'))
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

            mensagem = "METADADOS for the WFS0.4 filesystem\n\n" \
                       "Number of fragments: {0}\n" \
                       "Number of videos: {1}\n" \
                       "Standard fragment size: {2}\n" \
                       "Number of reserved fragment: {3}\n" \
                       "Reserved area before data area: {4:.0f} MB".format(self.qtd_frag, len(self.lista_principais), self.fragmento,
                                                                       self.qtd_reservados, self.qtd_reservados*self.fragmento/1048576)
            wx.MessageBox(mensagem, "WFS0.4 Metadata", style=wx.OK)
        else:
            wx.MessageBox("No image/disk loaded!!!!!!", "Warning", style=wx.OK)

    # Separar todos os descritores principais
    def desc_principais(self):
        self.SetStatusText("Loading...")
        self.lista_principais = []
        self.disco.seek(self.inicio_descritores)
        for i in range(self.qtd_frag):
            descritor = self.disco.read(self.desc)
            dic = self.decodeBlockStructure(descritor)
            if (dic['attrib'] == 2 or dic['attrib'] == 3) and dic['begTimeStamp'] != dic['endTimeStamp']:
                self.lista_principais.append(descritor)

        print (len(self.lista_principais))
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
        if self.lb_datas.GetStringSelection() == "Todos":
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

        if dic['totBlocks'] > 1:
            pedacos = [dic['beginBlock'], dic['nextBlock']]
            for i in range(dic['totBlocks']):
                self.disco.seek(dic['nextBlock'] * self.desc + self.inicio_descritores)
                descritor = self.disco.read(self.desc)
                dic = self.decodeBlockStructure(descritor)

                if dic['nextBlock'] > 0:
                    pedacos.append(dic['nextBlock'])

        else: # caso o vídeo possua apenas 1 fragmento, salva apenas este
            pedacos = [dic['beginBlock']]

        return pedacos, ultimo

    def recupera_videos(self):
        if len(self.lista) == 0:
            wx.MessageBox("Choose a video", version, style=wx.OK | wx.ICON_INFORMATION)
        else:
            # Verifica a plataforma para formatar o caminho
            if platform.system() == 'Windows':
                try:
                    os.mkdir(os.getcwd()+"\\WFS0.4_Extractor")
                    caminho = os.getcwd()+"\\WFS0.4_Extractor\\"
                except FileExistsError:
                    caminho = os.getcwd()+"/WFS0.4_Extractor\\"
            else:
                try:
                    os.mkdir(os.getcwd()+"/WFS0.4_Extractor")
                    caminho = os.getcwd()+"/WFS0.4_Extractor/"
                except FileExistsError:
                    caminho = os.getcwd()+"/WFS0.4_Extractor/"


            for l in range(len(self.lista)):
                self.SetStatusText("Saving vídeo {0} in folder {1}".format(self.lista_meta[self.lista[l]], caminho))
                nome = (self.lista_meta[self.lista[l]]+".h264").replace(":","-")
                arq = open(caminho+nome, "wb")
                pedacos, ultimo = self.guarda_pos(self.primeira[self.lista[l]])
                #print(pedacos)

                for i in range(len(pedacos) - 1):
                    desloc = self.inicio_videos + pedacos[i] * self.fragmento
                    self.disco.seek(desloc)
                    frag = self.disco.read(self.fragmento)
                    arq.write(frag)

                desloc = self.inicio_videos + pedacos[-1] * self.fragmento
                self.disco.seek(desloc)
                frag = self.disco.read(ultimo)
                arq.write(frag)
                arq.close()

            wx.MessageBox("Video(s) sucessfully saved in folder {0}".format(caminho), style=wx.OK)

            self.SetStatusText("Done!!")

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
        print ("FIle:", self.combo.GetValue())
        self.Janela.carrega_imagem(self.combo.GetValue())

if __name__ == '__main__':
    app = wx.App()
    main = Janela(None)
    app.MainLoop()
