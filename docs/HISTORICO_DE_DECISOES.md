# Histórico de Decisões Arquiteturais

## Decisão 001 — Arquitetura única, omnichannel e multiempresa

### Data

Julho de 2026.

### Contexto

O Orion CRM AI começou como uma solução de atendimento e qualificação para a Forway, utilizando a Sofia SDR no WhatsApp.

Durante a definição da arquitetura futura, foi necessário decidir entre criar sistemas separados para WhatsApp, Instagram e Facebook ou utilizar um único núcleo para todos os canais.

### Decisão

Foi escolhida uma arquitetura única, omnichannel e multiempresa.

Todos os canais utilizarão o mesmo backend, banco de dados, motor de atendimento e dashboard.

As diferenças de cada canal serão tratadas por adaptadores de integração.

As diferenças entre empresas serão tratadas por configurações e regras associadas à empresa.

### Motivos

- evitar duplicação de código;
- facilitar manutenção;
- permitir expansão para novos canais;
- permitir expansão para novos clientes;
- centralizar clientes, conversas e leads;
- viabilizar a transformação do projeto em plataforma SaaS;
- criar uma base escalável para a Orion Systems.

### Impactos

A implementação atual da Forway deverá evoluir gradualmente para:

- identificação da empresa em todos os registros;
- isolamento de dados por empresa;
- configurações comerciais por empresa;
- configurações dos canais por empresa;
- autenticação e controle de permissões;
- remoção gradual de configurações fixas no código.

### Estado

Decisão aprovada.

A implementação completa ainda será realizada de forma progressiva.