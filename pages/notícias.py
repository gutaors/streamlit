import streamlit as st
import os
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Mapping of tickers to company names in Portuguese
TICKER_COMPANY_MAP = {
    "B3SA3.SA": "B3 Bolsa Brasil Balcão",
    "BBAS3.SA": "Banco do Brasil",
    "EMBR3.SA": "Embraer",
    "PETR4.SA": "Petrobras",
    "VALE3.SA": "Vale"
}

def get_available_tickers():
    """Get list of available tickers from cotacoes folder"""
    cotacoes_path = "cotacoes"
    tickers = []
    
    if os.path.exists(cotacoes_path):
        for file in os.listdir(cotacoes_path):
            if file.endswith('.csv'):
                # Remove .csv extension
                ticker = file.replace('.csv', '')
                tickers.append(ticker)
    
    return sorted(tickers)

def get_company_name(ticker):
    """Get company name from ticker"""
    return TICKER_COMPANY_MAP.get(ticker, ticker)

def search_google_news(company_name, ticker, selected_date=None, last_30_days=False):
    """Search Google News for articles about the company in Brazilian Portuguese"""
    try:
        # Format search query for Brazilian Portuguese news
        # Search for both company name and ticker
        search_terms = f"{company_name} OR {ticker.replace('.SA', '')}"
        
        # Google News RSS URL with Portuguese language filter
        base_url = "https://news.google.com/rss/search"
        params = {
            'q': search_terms,
            'hl': 'pt-BR',  # Brazilian Portuguese
            'gl': 'BR',      # Brazil region
            'ceid': 'BR:pt-419'  # Brazil Portuguese edition
        }
        
        # Build URL with parameters
        url = f"{base_url}?q={requests.utils.quote(search_terms)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        # Make request
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse RSS feed
        root = ET.fromstring(response.content)
        
        articles = []
        
        # Calculate date range for filtering
        if last_30_days:
            date_limit = datetime.now() - timedelta(days=30)
        
        # Find all items in the RSS feed
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate')
            description_elem = item.find('description')
            source_elem = item.find('source')
            
            if title_elem is not None and link_elem is not None:
                title = title_elem.text
                link = link_elem.text
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                description = description_elem.text if description_elem is not None else ""
                source = source_elem.text if source_elem is not None else "Google News"
                
                # Parse publication date
                try:
                    # Google News RSS uses RFC 822 format
                    article_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    try:
                        article_date = datetime.strptime(pub_date.split(' GMT')[0], '%a, %d %b %Y %H:%M:%S')
                    except:
                        article_date = None
                
                # Filter by selected date or last 30 days
                if last_30_days:
                    # Include articles from last 30 days
                    if article_date and article_date >= date_limit:
                        articles.append({
                            'title': title,
                            'link': link,
                            'date': pub_date,
                            'description': clean_html(description),
                            'source': source
                        })
                    elif not article_date:
                        # If we can't parse the date, include it anyway
                        articles.append({
                            'title': title,
                            'link': link,
                            'date': pub_date,
                            'description': clean_html(description),
                            'source': source
                        })
                elif selected_date:
                    # Filter by specific date (within same day)
                    if article_date:
                        if article_date.date() == selected_date:
                            articles.append({
                                'title': title,
                                'link': link,
                                'date': pub_date,
                                'description': clean_html(description),
                                'source': source
                            })
                    else:
                        # If we can't parse the date, include it anyway
                        articles.append({
                            'title': title,
                            'link': link,
                            'date': pub_date,
                            'description': clean_html(description),
                            'source': source
                        })
        
        # If no articles found for exact date and not using last_30_days, search for nearby dates
        if len(articles) == 0 and not last_30_days:
            for item in root.findall('.//item')[:10]:  # Get at least top 10 recent articles
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                description_elem = item.find('description')
                source_elem = item.find('source')
                
                if title_elem is not None and link_elem is not None:
                    articles.append({
                        'title': title_elem.text,
                        'link': link_elem.text,
                        'date': pub_date_elem.text if pub_date_elem is not None else "",
                        'description': clean_html(description_elem.text if description_elem is not None else ""),
                        'source': source_elem.text if source_elem is not None else "Google News"
                    })
        
        return articles
    
    except Exception as e:
        st.error(f"Erro ao buscar notícias: {str(e)}")
        return []

def clean_html(text):
    """Remove HTML tags from text"""
    if text:
        soup = BeautifulSoup(text, 'html.parser')
        # Get text and limit to first 200 characters
        clean_text = soup.get_text()
        if len(clean_text) > 200:
            return clean_text[:200] + "..."
        return clean_text
    return ""

# Page configuration
st.set_page_config(page_title="Notícias", page_icon="📰", layout="wide")

# Title
st.title("📰 Notícias do Mercado")
st.markdown("---")

# Get available tickers
tickers = get_available_tickers()

if not tickers:
    st.error("Nenhum ticker encontrado na pasta 'cotacoes'")
else:
    # Create two columns for ticker and date selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_ticker = st.selectbox(
            "Selecione o Ticker:",
            tickers,
            format_func=lambda x: f"{x} - {get_company_name(x)}"
        )
    
    with col2:
        date_option = st.radio(
            "Período:",
            options=["Data Específica", "Últimas"],
            horizontal=True
        )
        
        if date_option == "Data Específica":
            selected_date = st.date_input(
                "Selecione a Data:",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
        else:
            st.info("Serão exibidas notícias dos últimos 30 dias")
            selected_date = None
    
    # Search button
    if st.button("🔍 Buscar Notícias", type="primary"):
        if selected_ticker:
            company_name = get_company_name(selected_ticker)
            
            if date_option == "Últimas":
                with st.spinner(f"Buscando notícias dos últimos 30 dias sobre {company_name}..."):
                    articles = search_google_news(company_name, selected_ticker, last_30_days=True)
            else:
                with st.spinner(f"Buscando notícias sobre {company_name}..."):
                    articles = search_google_news(company_name, selected_ticker, selected_date=selected_date)
            
            if articles:
                st.success(f"Encontradas {len(articles)} notícia(s)")
                st.markdown("---")
                
                # Display articles
                for idx, article in enumerate(articles, 1):
                    # Create a container for each article
                    with st.container():
                        # Source name
                        st.markdown(f"**{article['source']}**")
                        
                        # Article title as header
                        st.subheader(f"Notícia {idx}")
                        st.markdown(f"**{article['title']}**")
                        
                        # Description/summary
                        if article['description']:
                            st.write(article['description'])
                        
                        # Publication date
                        if article['date']:
                            st.caption(f"📅 {article['date']}")
                        
                        # Link to full article
                        st.markdown(f"[🔗 Ler notícia completa]({article['link']})")
                        
                        st.markdown("---")
            else:
                if date_option == "Últimas":
                    st.warning(f"Nenhuma notícia encontrada para {company_name} nos últimos 30 dias. Tente outro ticker.")
                else:
                    st.warning(f"Nenhuma notícia encontrada para {company_name} na data {selected_date.strftime('%d/%m/%Y')}. Tente outra data ou selecione 'Últimas'.")
        else:
            st.error("Por favor, selecione um ticker.")

# Add information about the news source
with st.expander("ℹ️ Sobre as notícias"):
    st.markdown("""
    **Fonte:** Google News (Brasil)
    
    As notícias são coletadas do Google News com filtro para o Brasil e idioma português brasileiro.
    
    **Nota:** As notícias exibidas são de fontes públicas e respeitáveis indexadas pelo Google News.
    """)
