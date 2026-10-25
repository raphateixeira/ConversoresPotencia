# Referências — Microrredes

PDFs guardados na biblioteca Calibre **`~/Livros/Microgrids`**. Todos têm a tag
`Microrredes` e uma tag da seção: `Visão geral e controle hierárquico`, `Livro`,
`Dados — primária`, `Dados — secundária`, `Dados — terciária` ou `Contexto Amazônia`.
`#n` é o id do livro no Calibre e o caminho é relativo à biblioteca.

```bash
open "$HOME/Livros/Microgrids/<caminho>"            # abre o PDF
calibredb list --library-path ~/Livros/Microgrids -s "tags:\"Dados — primária\""
```

Legenda: 📚 PDF no Calibre · ⛔ sem PDF (acesso pago, conseguir pelo Portal CAPES) · 🔗 acesso aberto, baixar à mão.
As chaves `[chave]` correspondem a [Referencias.bib](Referencias.bib).

## Visão geral e controle hierárquico

- ⛔ [guerrero2011] Guerrero, Vasquez, Matas, de Vicuña & Castilla (2011). *Hierarchical Control of Droop-Controlled AC and DC Microgrids — A General Approach Toward Standardization*. IEEE TIE 58(1). DOI: 10.1109/TIE.2010.2066534
- 📚 #4 [guerrero2013] Guerrero, Chandorkar, Lee & Loh (2013). *Advanced Control Architectures for Intelligent Microgrids — Part I: Decentralized and Hierarchical Control*. IEEE TIE 60(4). DOI: 10.1109/TIE.2012.2194969
  `Josep M. Guerrero/Advanced Control Architectures for Intelligent Microgrids -- Part I_ Decentralized and Hierarchi (4)/Advanced Control Architectures for Intelli - Josep M. Guerrero.pdf`
- ⛔ [rocabert2012] Rocabert, Luna, Blaabjerg & Rodríguez (2012). *Control of Power Converters in AC Microgrids*. IEEE TPEL 27(11). DOI: 10.1109/TPEL.2012.2199334
- ⛔ [olivares2014] Olivares et al. (2014). *Trends in Microgrid Control*. IEEE TSG 5(4). DOI: 10.1109/TSG.2013.2295514
- ⛔ [parisio2014] Parisio, Rikos & Glielmo (2014). *A Model Predictive Control Approach to Microgrid Operation Optimization*. IEEE TCST 22(5). DOI: 10.1109/TCST.2013.2295737. O repositório de Manchester tem a versão aceita, mas exige login.
- ⛔ [milano2018] Milano, Dörfler, Hug, Hill & Verbič (2018). *Foundations and Challenges of Low-Inertia Systems*. PSCC. DOI: 10.23919/PSCC.2018.8450880. O ResearchGate bloqueia download automático; tentar à mão: <https://repository.hku.hk/handle/10722/263530>
- 📚 #5 [dorfler2023] Dörfler & Groß (2023). *Control of Low-Inertia Power Systems*. Annual Review of Control, Robotics, and Autonomous Systems 6. DOI: 10.1146/annurev-control-052622-032657
  `Florian Dorfler/Control of Low-Inertia Power Systems (5)/Control of Low-Inertia Power Systems - Florian Dorfler.pdf`
- 📚 #6 [zhao2021] Zhao, Blaabjerg & Wang (2021). *An Overview of Artificial Intelligence Applications for Power Electronics*. IEEE TPEL 36(4). DOI: 10.1109/TPEL.2020.3024914
  `Shuai Zhao/An Overview of Artificial Intelligence Applications for Power Electronics (6)/An Overview of Artificial Intelligence App - Shuai Zhao.pdf`

## Livros

- 📚 #7 [hatziargyriou2014] Hatziargyriou (ed.) (2014). *Microgrids: Architectures and Control*. Wiley-IEEE Press.
  `Nikos Hatziargyriou/Microgrids_ Architectures and Control (7)/Microgrids_ Architectures and Control - Nikos Hatziargyriou.pdf`
- 📚 #2 [yazdani2010] Yazdani & Iravani (2010). *Voltage-Sourced Converters in Power Systems*. Wiley-IEEE Press.
  `Amirnaser Yazdani, Reza Iravani/Voltage-Sourced Converters in Power Systems (2)/Voltage-Sourced Converters in Power System - Amirnaser Yazdani, Reza Iravani.pdf`
- 📚 #8 [bevrani2017] Bevrani, François & Ise (2017). *Microgrid Dynamics and Control*. Wiley.
  `Hassan Bevrani/Microgrid Dynamics and Control (8)/Microgrid Dynamics and Control - Hassan Bevrani.pdf`
- ⛔ [kundur2022] Kundur & Malik (2022). *Power System Stability and Control*, 2ª ed. McGraw-Hill.

## Controle baseado em dados — camada primária (conversor/rede)

- 📚 #9 [huang2019] Huang, Coulson, Lygeros & Dörfler (2019). *Data-Enabled Predictive Control for Grid-Connected Power Converters*. CDC. arXiv:1903.07339
  `Linbin Huang/Data-Enabled Predictive Control for Grid-Connected Power Converters (9)/Data-Enabled Predictive Control for Grid-C - Linbin Huang.pdf`
- 📚 #10 [zhao2024] Zhao, Leng, Huang, Xin, You & Dörfler (2024). *Direct Adaptive Control of Grid-Connected Power Converters via Output-Feedback Data-Enabled Policy Optimization*. arXiv:2411.03909
  `Feiran Zhao/Direct Adaptive Control of Grid-Connected Power Converters via Output-Feedback Data-Enabled Poli (10)/Direct Adaptive Control of Grid-Connected - Feiran Zhao.pdf`
- 📚 #11 [roinila2016] Roinila, Luhtala, Reinikka, Messo & Aapro (2016). *dSPACE Implementation for Real-Time Stability Analysis of Three-Phase Grid-Connected Systems Applying MLBS Injection*. EUROSIM 2016, LiU ECP 142.
  `Tomi Roinila/dSPACE Implementation for Real-Time Stability Analysis of Three-Phase Grid-Connected Systems App (11)/dSPACE Implementation for Real-Time Stabil - Tomi Roinila.pdf`
- 🔗 [alenius2020] Alenius, Luhtala & Roinila (2020). *Amplitude Design of Perturbation Signal in Frequency-Domain Analysis of Grid-Connected Systems*. IFAC-PapersOnLine 53(2). DOI: 10.1016/j.ifacol.2020.12.123. É acesso aberto, mas o servidor do IFAC 2020 e o repositório de Tampere bloquearam o download automático.
- 📚 #12 [neshvad2014] Neshvad, Chatzinotas & Sachau (2014). *Online Determination of Grid Impedance Spectrum through Pseudo-Random Excitation of a Pulse Width Modulator*. RE&PQJ (ICREPQ'14). DOI: 10.24084/repqj12.323
  `Surena Neshvad/Online Determination of Grid Impedance Spectrum through Pseudo-Random Excitation of a Pulse Widt (12)/Online Determination of Grid Impedance Spe - Surena Neshvad.pdf`

## Controle baseado em dados — camada secundária (dinâmica do conjunto)

- ⛔ [barocio2015] Barocio, Pal, Thornhill & Messina (2015). *A Dynamic Mode Decomposition Framework for Global Power System Oscillation Analysis*. IEEE TPWRS 30(6). DOI: 10.1109/TPWRS.2014.2368078
- 📚 #13 [du2025] Du & Wang (2025). *A Data-Driven Method for Microgrid System Identification: Physically Consistent Sparse Identification of Nonlinear Dynamics*. arXiv:2502.09592
  `Mohan Du/A Data-Driven Method for Microgrid System Identification_ Physically Consistent Sparse Identific (13)/A Data-Driven Method for Microgrid System - Mohan Du.pdf`
  Relacionado, na biblioteca `Papers` (#8): Du, Lai, Liu & Wang, *Physically Consistent SINDy for Microgrid Identification and Real-Time Frequency Control*.
- 📚 #14 [wolf2024] Wolf & Hans (2024). *Identification of Power Systems with Droop-Controlled Units Using Neural Ordinary Differential Equations*. arXiv:2411.08678
  `Hannes M. H. Wolf/Identification of Power Systems with Droop-Controlled Units Using Neural Ordinary Differential E (14)/Identification of Power Systems with Droop - Hannes M. H. Wolf.pdf`
- 📚 #15 [hosseinipour2024] Hosseinipour & Khazaei. *Sparse Identification for Data-Driven Dynamics and Impedance Modeling of Power Converters in DC Microgrids*. NSF PAR 10513219.
  `Ali Hosseinipour/Sparse Identification for Data-Driven Dynamics and Impedance Modeling of Power Converters in DC (15)/Sparse Identification for Data-Driven Dyna - Ali Hosseinipour.pdf`
- 📚 #16 [khazaei2023] Khazaei & Hosseinipour. *Data-Driven Feedback Linearization Control of Distributed Energy Resources using Sparse Regression*. NSF PAR 10439383.
  `Javad Khazaei/Data-Driven Feedback Linearization Control of Distributed Energy Resources using Sparse Regressi (16)/Data-Driven Feedback Linearization Control - Javad Khazaei.pdf`

## Controle baseado em dados — camada terciária (gestão de energia)

- 📚 #17 [barbalho2025] Barbalho, Moraes, Lacerda, Barra, Fernandes & Coury (2025). *Reinforcement Learning Solutions for Microgrid Control and Management: A Survey*. IEEE Access 13. DOI: 10.1109/ACCESS.2025.3546578
  `Pedro I. N. Barbalho/Reinforcement Learning Solutions for Microgrid Control and Management_ A Survey (17)/Reinforcement Learning Solutions for Micro - Pedro I. N. Barbalho.pdf`
- 📚 #18 [mohammadi2024] Mohammadi, Darshi, Shamaghdari & Siano (2024). *Comparative Analysis of Control Strategies for Microgrid Energy Management with a Focus on Reinforcement Learning*. IEEE Access 12. DOI: 10.1109/ACCESS.2024.3495032
  `Parisa Mohammadi/Comparative Analysis of Control Strategies for Microgrid Energy Management with a Focus on Reinf (18)/Comparative Analysis of Control Strategies - Parisa Mohammadi.pdf`
- 📚 #19 [arwa2020] Arwa & Folly (2020). *Reinforcement Learning Techniques for Optimal Power Control in Grid-Connected Microgrids: A Comprehensive Review*. IEEE Access 8. DOI: 10.1109/ACCESS.2020.3038735
  `Erick O. Arwa/Reinforcement Learning Techniques for Optimal Power Control in Grid-Connected Microgrids_ A Comp (19)/Reinforcement Learning Techniques for Opti - Erick O. Arwa.pdf`

## Contexto: acesso à energia e Amazônia

- 📚 #20 [esmap2022] ESMAP/Banco Mundial (2022). *Mini Grids for Half a Billion People: Market Outlook and Handbook for Decision Makers*. hdl:10986/38082
  `ESMAP/Mini Grids for Half a Billion People_ Market Outlook and Handbook for Decision Makers (20)/Mini Grids for Half a Billion People_ Mark - ESMAP.pdf`
- 📚 #21 [iema2021] IEMA (2021). *Exclusão elétrica na Amazônia Legal: quem ainda está sem acesso à energia elétrica?*
  `IEMA/Exclusao eletrica na Amazonia Legal_ quem ainda esta sem acesso a energia eletrica_ (21)/Exclusao eletrica na Amazonia Legal_ quem - IEMA.pdf`
- 📚 #22 [iema2026] IEMA (2026). *Políticas públicas e experiências de acesso à energia: da agenda internacional às soluções comunitárias na Pan-Amazônia*.
  `IEMA/Politicas publicas e experiencias de acesso a energia_ da agenda internacional as solucoes comun (22)/Politicas publicas e experiencias de acess - IEMA.pdf`
- 📚 #23 [idec2024] Idec (2024). *No escuro da floresta: situação de exclusão energética na Amazônia Legal e lacunas nas políticas públicas de acesso à energia*.
  `Idec/No escuro da floresta_ situacao de exclusao energetica na Amazonia Legal e lacunas nas politicas (23)/No escuro da floresta_ situacao de exclusa - Idec.pdf`
