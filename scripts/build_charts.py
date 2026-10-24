"""Generate accurate vector previews from public companion-book data/equations."""
import argparse,csv,json,math,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--book',type=Path,default=ROOT.parent/'macro102-site');a=p.parse_args()
blue='#8dcaff';coral='#ffa698';lavender='#bcaaff';muted='#a6b4cc';navy='#0d192d'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'text.color':muted,'axes.labelcolor':muted,'xtick.color':muted,'ytick.color':muted,'svg.fonttype':'none'})
def setup(ylabel):
 fig,ax=plt.subplots(figsize=(6.4,3.6));fig.patch.set_facecolor(navy);ax.set_facecolor(navy)
 ax.spines[['top','right','left']].set_visible(False);ax.spines['bottom'].set_color('#31435d');ax.grid(axis='y',color='#26364d',lw=.7);ax.set_axisbelow(True);ax.tick_params(length=0,pad=8);ax.set_ylabel(ylabel,labelpad=12,fontsize=12)
 return fig,ax
def save(fig,name):
 fig.tight_layout(pad=1.5);fig.savefig(ROOT/f'assets/charts/{name}.svg',transparent=True);plt.close(fig)
 path=ROOT/f'assets/charts/{name}.svg';path.write_text("\n".join(line.rstrip() for line in path.read_text().replace("font-family: 'DejaVu Sans'","font-family: Arial, sans-serif").splitlines())+"\n")
def rows(path):
 dst=ROOT/'data'/Path(path).name;shutil.copy2(a.book/'data'/path,dst)
 return list(csv.DictReader(dst.open()))
# Cross-country levels from the book's Maddison Project panel, common 2022 endpoint.
r=rows('ch03/maddison_panel.csv');names=['United States','Japan','China','India'];colors=[blue,lavender,coral,'#8de0c1']
f,ax=setup('GDP per person · 2022 international $')
for name,c in zip(names,colors):
 pts=[d for d in r if d['country']==name and 1950<=int(d['year'])<=2022]
 assert pts,name
 ax.plot([int(d['year']) for d in pts],[float(d['gdppc'])/1000 for d in pts],label=name,c=c,lw=2.4)
ax.set_ylabel('GDP per person · thousand 2022 int. $',fontsize=12);ax.legend(frameon=False,labelcolor=muted,fontsize=10,ncol=2,loc='upper left');save(f,'growth')
r=rows('ch10/fig10-8.csv');f,ax=setup('Output relative to potential · %')
xs=[int(d['date'][:4])+(int(d['date'][5:7])-1)/12 for d in r];ys=[float(d['short_run_output']) for d in r]
ax.axhline(0,c=muted,lw=.7,ls='--');ax.plot(xs,ys,c=blue,lw=2.3);ax.fill_between(xs,ys,0,color=blue,alpha=.10);ax.text(2009,-5.7,'Financial crisis',color=coral,fontsize=10);ax.text(2018,-9.5,'Pandemic',color=coral,fontsize=10);save(f,'recessions')
r=rows('ch08/fig8-1.csv');f,ax=setup('U.S. consumer price inflation · % / year');ax.plot([int(d['year']) for d in r],[float(d['inflation_cpi']) for d in r],c=coral,lw=2.3);ax.axhline(0,c=muted,lw=.7);save(f,'inflation')
f,ax=setup('Unemployment · % of labor force');s=.01;find=.20;steady=s/(s+find);u=.10;values=[u*100]
for month in range(24):u=s+(1-s-find)*u;values.append(u*100)
ax.plot(range(25),values,c=blue,lw=2.5,label='After a shock');ax.axhline(steady*100,c=coral,ls='--',lw=1.5,label=f'Natural rate: {steady*100:.2f}%');ax.set_xlabel('Months');ax.legend(frameon=False,labelcolor=muted,fontsize=12);save(f,'employment')
f,ax=setup('Inflation · %');x=[-2+i*.04 for i in range(101)];ax.plot(x,[2-v for v in x],c=blue,lw=2.4,label='Aggregate demand');ax.plot(x,[2+v for v in x],c=coral,lw=2.4,label='Aggregate supply');ax.scatter([0],[2],s=45,c='white',zorder=3);ax.axvline(0,c=muted,ls=':',lw=.7);ax.set_xlabel('Output relative to potential · %');ax.legend(frameon=False,labelcolor=muted,fontsize=10);save(f,'policy')
f,ax=setup('Foreign currency per U.S. dollar');rates=[i*.1 for i in range(101)];fx=[.92*(1+i/100)/(1+.05) for i in rates];ax.plot(rates,fx,c=lavender,lw=2.4);ax.scatter([6],[.92*1.06/1.05],c=coral,s=40,zorder=3);ax.set_xlabel('U.S. interest rate · %');ax.text(.4,.955,'Foreign rate = 5% · expected exchange rate = 0.92',fontsize=10,color=muted);save(f,'global')
(ROOT/'data/chart-sources.json').write_text(json.dumps({
'growth':{'source':'Chapter 3, Maddison Project Database 2023','file':'maddison_panel.csv','selection':'United States, Japan, China, India; 1950–2022','unit':'GDP per capita in 2022 international dollars; plotted in thousands'},
'recessions':{'source':'Chapter 10, Figure 8; BEA/CBO via FRED','file':'fig10-8.csv','column':'short_run_output'},
'inflation':{'source':'Chapter 8, Figure 1; FRED CPIAUCSL, annual-average CPI-U inflation','file':'fig8-1.csv','column':'inflation_cpi'},
'employment':{'source':'Chapter 7, bathtub model','equation':'u[t+1] = s + (1-s-f)u[t]','parameters':{'s':.01,'f':.20,'u0':.10}},
'policy':{'source':'Chapter 13, AS/AD framework','equations':['Y = -b*m*(pi-pi_bar)','pi = pi_e + nu*Y'],'parameters':{'pi_bar':2,'pi_e':2,'b':2,'m':.5,'nu':1}},
'global':{'source':'Chapter 20, equation 7: uncovered interest parity','equation':'E = E_expected * (1+i/100)/(1+i_foreign/100)','parameters':{'E_expected':.92,'i_foreign':5,'highlight_i':6}}
},indent=2)+'\n')
print('Built six source-traceable SVG charts.')
