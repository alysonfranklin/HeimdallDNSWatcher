# Heimdall DNS Watcher

O Heimdall DNS Watcher é um aplicativo Python inteligente e vigilante que atua como um guardião entre o cluster Kubernetes e o Cloudflare DNS. Ele monitora continuamente os recursos `IngressRoute` no Kubernetes, observando atentamente qualquer mudança ou novo evento.

Quando um novo IngressRoute é criado no Kubernetes, o `Heimdall DNS Watcher` entra em ação. Ele analisa meticulosamente as labels do IngressRoute, procurando por uma combinação específica que indica a necessidade de gerenciamento de DNS. Se houver uma correspondência, o Heimdall DNS Watcher extrai o nome de host especificado no campo `host` do IngressRoute.

Com o nome de host em mãos, o Heimdall DNS Watcher se comunica com o `Cloudflare`. Ele cria um novo registro DNS CNAME no Cloudflare, vinculando o nome de host extraído do IngressRoute a um endereço CNAME de destino predefinido. Esse processo automatizado garante que o registro DNS esteja sempre em sincronia com o IngressRoute correspondente no Kubernetes.

Além de criar novos registros DNS, o Heimdall DNS Watcher também é responsável por atualizar e excluir registros quando ocorrem mudanças nos IngressRoutes. Se um IngressRoute for modificado, o Heimdall DNS Watcher detectará a mudança e atualizará o registro DNS correspondente no Cloudflare para refletir as novas informações. Da mesma forma, se um IngressRoute for `excluído`, o Heimdall DNS Watcher removerá prontamente o registro DNS associado no Cloudflare.

Com sua vigilância constante e automação inteligente, o Heimdall DNS Watcher simplifica o gerenciamento de DNS para aplicativos Kubernetes que utilizam o `Traefik` como Ingress Controller. Ele garante que os registros DNS no Cloudflare estejam sempre em sincronia com os recursos IngressRoute no Kubernetes, eliminando a necessidade de intervenção manual e reduzindo a possibilidade de erros.

## Por que o nome da aplicação é Heimdall?

Heimdall é o **guardião** dos deuses na mitologia nórdica, conhecido por sua vigilância e capacidade de **ver e ouvir tudo**. Assim como Heimdall vigia Asgard, essa aplicação monitora constantemente os eventos do Kubernetes IngressRoute e toma as ações apropriadas nos registros DNS.

## Funcionalidades

- Monitora eventos de criação, modificação e exclusão de IngressRoutes no cluster Kubernetes.
- Extrai informações relevantes dos IngressRoutes, como o nome do host e as labels.
- Cria, atualiza ou exclui registros DNS CNAME no Cloudflare com base nas mudanças nos IngressRoutes.
- Configura o status do proxy (ativado ou desativado) para cada registro DNS com base na label 'proxyEnabled' do IngressRoute.
- Registra todas as ações e erros usando o módulo de logging do Python.

## Pré-requisitos

Antes de executar a aplicação, certifique-se de ter os seguintes pré-requisitos:

- Um cluster Kubernetes em execução e configurado.
- Uma conta no Cloudflare com permissões para gerenciar registros DNS.
- Um token de API do Cloudflare com permissões para ler e gravar registros DNS.

## Configuração

1. Clone este repositório para o seu ambiente local.

2. Defina as seguintes variáveis de ambiente no arquivo `values.yaml`:

- `CLOUDFLARE_API_TOKEN`: O token de API do Cloudflare com permissões para ler e gravar registros DNS.
- `CLOUDFLARE_ZONE_ID`: O ID da zona DNS no Cloudflare onde os registros serão gerenciados.
- `TARGET_CNAME_ADDRESS`: O endereço CNAME de destino para os registros DNS criados. Pode ser DNS do loadbalancer do ingress, endpoint do AWS CloudFront, AWS API Gateway, etc.
- `LOG_LEVEL` (opcional): O nível de log desejado (por exemplo, INFO, DEBUG). O padrão é INFO.


3. Instale a aplicação Heimdall em seu Cluster Kubernetes via helm
```bash
$ helm upgrade --install heimdall ./heimdall
```

Aguarde a aplicação ficar `Running` e visualize os logs dela
```bash
$ kubectl logs -f -l app=heimdall-dns-watcher
```

4. Instale a aplicação Heimdall via Kubectl

**Antes de instalar via Kubectl, é necessário informar seus dados de conexão no arquivo manifest/secret.yaml**

```bash
$ kubectl apply -f ./manifest/ --recursive

# Para visualizar o log da aplicação:
$ kubectl logs -f -l app=heimdall-dns-watcher
```

5. Crie o IngressRoute

Agora abra outro terminal e crie o ingressRoute com o seguinte comando:
```bash
$ kubectl apply -f ingressroute.yaml
```

Após a criação do ingressRoute, você verá no log da aplicação a informação de criação de DNS no CloudFlare.
<img width="873" alt="Create ingressroute" src="https://github.com/user-attachments/assets/f6e6c003-af7f-4b56-b1b8-d0f70a61c74f">

Agora vamos editar o ingressroute.yaml, desabilitar o proxy e executar novamente `kubectl apply -f ingressroute.yaml`
<img width="933" alt="Screenshot 2024-08-30 at 11 01 41" src="https://github.com/user-attachments/assets/f5bf095a-af2f-445f-a770-36d8525eb981">

Hora de excluir ingressroute com `kubectl delete -f ingressroute.yaml`.
No momento que você exclui o ingressroute, a aplicação identifica esse evento e entende que precisa excluir a entrada DNS do **CloudFlare**
<img width="868" alt="Screenshot 2024-08-30 at 11 01 41" src="https://github.com/user-attachments/assets/8cc16903-a545-42eb-a995-03ea8d9ff1bf">

# Contribuição
Contribuições são bem-vindas! Se você encontrar algum problema, tiver sugestões ou quiser adicionar novos recursos, fique à vontade para abrir uma issue ou enviar um pull request.

# Licença
Este projeto está licenciado sob a MIT License.
