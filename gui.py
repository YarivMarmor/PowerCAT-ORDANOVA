import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, csv
from .core import load_counts, analyze
from .validation import validate_design
from .charts import make_figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PowerCAT / ORDANOVA - Research Preview v0.5.0')
        self.geometry('1180x810')
        self.data = None; self.result = None; self.charts = {}; self.preflight_ok = False
        self.path = tk.StringVar(value='No file selected')
        self.mode = tk.StringVar(value='Ordinal')
        self.alpha = tk.StringVar(value='0.05')
        self.w = tk.StringVar(value='0.3')
        self.runs = tk.StringVar(value='10000')
        self.seed = tk.StringVar(value='12345')
        self.status = tk.StringVar(value='Load an I,J,K,Y file to begin')
        self.bin_mode = tk.StringVar(value='auto')
        self.manual_bins = tk.StringVar(value='80')
        self.display_range = tk.StringVar(value='99.5')
        self.series = tk.StringVar(value='Both')
        self.markers = tk.BooleanVar(value=False)
        self.pdf_display = tk.StringVar(value='Both')
        self.smoothing = tk.StringVar(value='1.0')
        root=ttk.Frame(self,padding=12);root.pack(fill='both',expand=True)
        ttk.Label(root,text='PowerCAT / ORDANOVA',font=('Segoe UI',19,'bold')).pack(anchor='w')
        ttk.Label(root,text='Research preview - Monte Carlo results still require VBA validation',foreground='#905c13').pack(anchor='w',pady=(0,6))
        bar=ttk.Frame(root);bar.pack(fill='x',pady=5)
        ttk.Button(bar,text='Open data file',command=self.open_file).pack(side='left')
        ttk.Button(bar,text='Review data / design',command=self.review_data).pack(side='left',padx=6)
        ttk.Label(bar,textvariable=self.path).pack(side='left',padx=12)
        opts=ttk.Frame(root);opts.pack(fill='x',pady=5)
        for title,var,values in [('Type',self.mode,['Ordinal','Nominal']),('Iterations',self.runs,None),('Alpha',self.alpha,None),('w',self.w,None),('Seed',self.seed,None)]:
            block=ttk.Frame(opts);block.pack(side='left',padx=7)
            ttk.Label(block,text=title).pack(anchor='w')
            control=ttk.Combobox(block,textvariable=var,values=values,state='readonly',width=12) if values else ttk.Entry(block,textvariable=var,width=13)
            control.pack()
        self.run_button=ttk.Button(opts,text='Run analysis',command=self.run)
        self.run_button.pack(side='left',padx=8,pady=10)
        self.run_button.configure(state='disabled')
        self.mode.trace_add('write',lambda *_:self._mode_changed())
        ttk.Button(opts,text='Export results CSV',command=self.export).pack(side='left')
        ttk.Label(root,textvariable=self.status).pack(anchor='w',pady=4)
        self.progress=ttk.Progressbar(root,mode='determinate',maximum=100);self.progress.pack(fill='x')
        self.table=ttk.Treeview(root,columns=('v','df','si','p','crit','power'),show='tree headings',height=6)
        self.table.heading('#0',text='Component');self.table.column('#0',width=100)
        for k,label,width in [('v','Variation',130),('df','df',70),('si','SI',120),('p','p-value',120),('crit','SI critical',120),('power','Power',120)]:
            self.table.heading(k,text=label);self.table.column(k,width=width,anchor='center')
        self.table.pack(fill='x',pady=8)
        controls=ttk.LabelFrame(root,text='Graph display (changes do not rerun or alter the statistical analysis)',padding=8)
        controls.pack(fill='x',pady=(2,5))
        self._labeled_choice(controls,'Bins',self.bin_mode,['auto','manual'],0)
        b=ttk.Frame(controls);b.grid(row=0,column=1,padx=8,sticky='w')
        ttk.Label(b,text='Manual bins').pack(anchor='w')
        self.bin_entry=ttk.Entry(b,textvariable=self.manual_bins,width=9);self.bin_entry.pack()
        self._labeled_choice(controls,'X range',self.display_range,['99.5','99','full'],2)
        self._labeled_choice(controls,'Components',self.series,['Both','A','B','AB'],3)
        ttk.Checkbutton(controls,text='Observed & critical lines',variable=self.markers).grid(row=0,column=4,padx=7)
        ttk.Button(controls,text='Update graphs',command=self.redraw).grid(row=0,column=5,padx=9)
        ttk.Button(controls,text='Export graph',command=self.export_graph).grid(row=0,column=6,padx=4)
        smoothrow=ttk.Frame(controls); smoothrow.grid(row=1,column=0,columnspan=7,sticky='w',pady=(8,0))
        ttk.Label(smoothrow,text='PDF curves').pack(side='left',padx=(7,5))
        ttk.Combobox(smoothrow,textvariable=self.pdf_display,values=['Both','Empirical','Smoothed'],state='readonly',width=13).pack(side='left')
        ttk.Label(smoothrow,text='Smooth bandwidth (0.2-5; 1 = auto)').pack(side='left',padx=(18,5))
        ttk.Entry(smoothrow,textvariable=self.smoothing,width=6).pack(side='left')
        ttk.Label(smoothrow,text='Solid = empirical; dashed = reflected KDE (x >= 0). Display only.').pack(side='left',padx=15)
        self.chart_tabs=ttk.Notebook(root);self.chart_tabs.pack(fill='both',expand=True)
        self.chart_tabs.bind('<<NotebookTabChanged>>',self._on_tab_change)
    def _labeled_choice(self,parent,label,var,values,column):
        block=ttk.Frame(parent);block.grid(row=0,column=column,padx=7,sticky='w')
        ttk.Label(block,text=label).pack(anchor='w')
        ttk.Combobox(block,textvariable=var,values=values,state='readonly',width=11).pack()
    def _mode_changed(self):
        self.preflight_ok=False
        self.run_button.configure(state='disabled')
        if self.data is not None:
            self.status.set('Analysis type changed. Review and confirm the design again.')

    def _clear_previous(self):
        self.result=None
        for item in self.table.get_children(): self.table.delete(item)
        for tab in self.chart_tabs.tabs():
            self.chart_tabs.forget(tab)
            self.nametowidget(tab).destroy()
        self.charts={}

    def open_file(self):
        name=filedialog.askopenfilename(filetypes=[('Text or CSV files','*.txt *.csv'),('All files','*.*')])
        if not name:return
        self.preflight_ok=False
        self.run_button.configure(state='disabled')
        self._clear_previous()
        self.data=None
        try:self.data=load_counts(name)
        except Exception as ex:
            self.path.set(name)
            self.status.set('Input validation failed. Correct the source file and open it again.')
            messagebox.showerror('Input error - fix the source file',str(ex)+'\n\nPlease correct your data file and use Open data file again.')
            return
        self.path.set(name)
        self.review_data()

    def review_data(self):
        if self.data is None:
            messagebox.showinfo('No data','Please open a data file first.')
            return
        self.preflight_ok=False
        self.run_button.configure(state='disabled')
        p=validate_design(self.data,self.mode.get())
        text=(f'Model: {p.model}\n'
              f'Factors: {p.factors}\n'
              f'Factor A levels (I): {p.levels_a}\n'
              f'Factor B levels (J): {p.levels_b if p.factors==2 else "Not applicable"}\n'
              f'Response categories (K): {p.categories}\n'
              f'Observations: {p.observations:,}\n'
              f'Sample size per cell/group: {p.sample_min}-{p.sample_max}\n'
              f'Replication: {p.replication}\n'
              f'Interaction A x B: {"Estimable" if p.interaction else "Not estimated"}\n')
        if p.errors:
            self.status.set('Design NOT supported; see validation errors.')
            messagebox.showerror('Design cannot be analysed',text+'\nErrors to correct / model limitations:\n- '+'\n- '.join(p.errors))
            return
        if p.warnings:text+='\nImportant notes:\n- '+'\n- '.join(p.warnings)+'\n'
        text+='\nDoes this match your experiment? Select Yes to enable Run analysis.'
        if messagebox.askyesno('Review experiment design before analysis',text):
            self.preflight_ok=True
            self.run_button.configure(state='normal')
            self.status.set('Design confirmed: '+p.model+f' | {p.observations:,} observations. Ready to analyse.')
        else:
            self.status.set('Design not confirmed. Select the correct type or open a corrected file.')

    def run(self):
        if self.data is None:messagebox.showinfo('No data','Open a data file first');return
        if not self.preflight_ok:messagebox.showwarning('Review required','Review and confirm the experiment design before analysis.');return
        try:params=(self.mode.get(),float(self.alpha.get()),float(self.w.get()),int(self.runs.get()),int(self.seed.get()))
        except ValueError:messagebox.showerror('Parameters','Invalid parameter values');return
        self.run_button.configure(state='disabled');self.progress['value']=0
        self.status.set('Running Monte Carlo simulation ...')
        def worker():
            try:
                result=analyze(self.data,*params,progress=lambda a,b:self.after(0,lambda a=a,b=b:self.progress.configure(value=100*a/b)))
                self.after(0,lambda:self.show_result(result))
            except Exception as ex:
                self.after(0,lambda e=str(ex):self._run_error(e))
        threading.Thread(target=worker,daemon=True).start()
    def _run_error(self,message):
        self.run_button.configure(state='normal' if self.preflight_ok else 'disabled');self.status.set('Analysis failed');messagebox.showerror('Analysis error',message)
    def show_result(self,res):
        self.run_button.configure(state='normal' if self.preflight_ok else 'disabled');self.result=res
        self.status.set(f'Finished: {res.iterations:,} simulations (seed {res.seed})')
        for item in self.table.get_children():self.table.delete(item)
        def fmt(n):return 'n/a' if n is None else f'{n:.5f}' if isinstance(n,float) else str(n)
        for key,v in res.observed.items():
            vals=('n/a',)*6 if v is None else tuple(fmt(v.get(c)) for c in ('variation','df','si'))+tuple(fmt(x.get(key)) for x in (res.p_values,res.critical,res.power))
            self.table.insert('','end',text=key,values=vals)
        self.redraw()
    def redraw(self):
        if self.result is None:return
        try:
            opts=dict(bin_mode=self.bin_mode.get(),manual_bins=int(self.manual_bins.get()),display_range=self.display_range.get(),series=self.series.get(),show_markers=self.markers.get(),pdf_display=self.pdf_display.get(),smoothing=float(self.smoothing.get()))
            figs={kind:make_figure(self.result,kind,**opts) for kind in ('PDF','CDF')}
        except Exception as ex:messagebox.showerror('Graph settings',str(ex));return
        for tab in self.chart_tabs.tabs():
            self.chart_tabs.forget(tab)
            self.nametowidget(tab).destroy()
        self.charts={}
        for kind,fig in figs.items():
            frame=ttk.Frame(self.chart_tabs);self.chart_tabs.add(frame,text=kind)
            canvas=FigureCanvasTkAgg(fig,master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both',expand=True)
            toolbar=NavigationToolbar2Tk(canvas,frame,pack_toolbar=False)
            toolbar.update();toolbar.pack(side='bottom',fill='x')
            self.charts[kind]=(fig,canvas)
    def _on_tab_change(self,_event):pass
    def export_graph(self):
        if not self.charts:return
        current=self.chart_tabs.tab(self.chart_tabs.select(),'text')
        p=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG image','*.png'),('SVG vector','*.svg'),('PDF vector','*.pdf')],initialfile=f'PowerCAT_{current}.png')
        if p:self.charts[current][0].savefig(p,dpi=300)
    def export(self):
        if self.result is None:return
        p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if not p:return
        r=self.result
        with open(p,'w',newline='',encoding='utf-8-sig') as f:
            wr=csv.writer(f);wr.writerow(['Type',r.mode,'Iterations',r.iterations,'seed',r.seed]);wr.writerow(['Component','Variation','df','SI','p-value','Critical','Power'])
            for key,v in r.observed.items():wr.writerow([key]+([v.get(x) for x in ('variation','df','si')] if v else ['n/a']*3)+[r.p_values.get(key),r.critical.get(key),r.power.get(key)])

def main():App().mainloop()
if __name__=='__main__':main()
