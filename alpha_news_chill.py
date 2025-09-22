"""
Enhanced Alpha Vantage News Generator with Style Selection System
- 5 distinct news presentation styles
- Improved gold/bitcoin filtering for market-relevant news only
- Stricter spam/legal content filtering
- Style-specific content generation
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import os
from dotenv import load_dotenv
from openai import OpenAI
import time

# Load environment variables
load_dotenv()


class ProfessionalNewsGenerator:
    def __init__(self, debug_mode=False):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.debug_mode = debug_mode

        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY required in .env file")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY required in .env file")

        self.base_url = "https://www.alphavantage.co/query"
        self.openai_client = OpenAI(api_key=self.openai_key)
        self.call_count = 0
        
        # Significance Filter Lists
        self.MAJOR_COMPANIES = [
            'apple', 'microsoft', 'google', 'amazon', 'tesla', 'nvidia', 'meta', 
            'netflix', 'intel', 'amd', 'disney', 'nike', 'cocacola', 'pepsi',
            'jpmorgan', 'goldman sachs', 'boeing', 'ford', 'exxon', 'chevron'
        ]
        
        self.HIGH_IMPACT_KEYWORDS = [
            'fed', 'federal reserve', 'interest rate', 'inflation', 'gdp', 'cpi',
            'jobs report', 'unemployment', 'trade war', 'tariffs', 'opec','gold',
            'market rally', 'market surge', 'market falls', 'record high',
            'dow', 'nasdaq', 's&p 500', 'oil prices', 'crude oil'
        ]
        
        # Style guide definitions
        self.style_guide = {
            "classic_daily": {
                "name": "Classic Daily Brief",
                "description": "Professional, conversational, structured daily update",
                "target_seconds": 65,
                "tone": "conversational yet authoritative",
                "pacing": "moderate"
            },
            "breaking_alert": {
                "name": "Breaking News Alert",
                "description": "Urgent, dramatic, immediate market developments",
                "target_seconds": 55,
                "tone": "urgent and dramatic",
                "pacing": "fast"
            },
            "weekly_deep": {
                "name": "Weekly Deep Dive",
                "description": "Analytical, comprehensive, forward-looking analysis",
                "target_seconds": 85,
                "tone": "analytical and comprehensive",
                "pacing": "slower, thoughtful"
            },
            "market_pulse": {
                "name": "Market Pulse",
                "description": "Energetic, rhythm-focused, punchy updates",
                "target_seconds": 60,
                "tone": "energetic and rhythmic",
                "pacing": "upbeat"
            },
            "strategic_outlook": {
                "name": "Strategic Outlook",
                "description": "Advisory, institutional, strategic positioning",
                "target_seconds": 80,
                "tone": "advisory and institutional",
                "pacing": "measured, authoritative"
            },
             "forex_briefing": {
        "name": "Forex Daily Briefing",
        "description": "Hard-data-driven analysis of major currency pairs and macroeconomic news.",
        "target_seconds": 50,
        "tone": "analytical and data-driven",
        "pacing": "clear and concise"
            }
        }

    # ===== Main Flow with Style Selection =====
    def generate_content(self, style_key="classic_daily") -> Dict[str, Any]:
        today = datetime.now().strftime('%A')
        print(f"📅 Generating {self.style_guide[style_key]['name']} content for {today}")

        if today == 'Monday':
            return self._generate_monday(style_key)
        elif today == 'Wednesday':
            return self._generate_wednesday(style_key)
        elif today == 'Friday':
            return self._generate_friday(style_key)
        else:
            return self._generate_generic(style_key)
    
    def get_available_styles(self) -> Dict[str, Dict]:
        """Return available styles with descriptions"""
        return {key: {
            "name": style["name"],
            "description": style["description"],
            "target_seconds": style["target_seconds"]
        } for key, style in self.style_guide.items()}

    # ===== Day Modes with Style Support =====
    def _generate_monday(self, style_key):
        news = self._get_high_quality_news(limit=8)
        market_data = self._get_market_snapshot()
        script, social_post, motion_script, video_caption, episode_title = self._generate_content_with_style(
            news, "Monday", "Weekly market open with key developments", style_key
        )
        return {
            'day': 'Monday',
            'type': 'Weekly Market Open',
            'style': self.style_guide[style_key]['name'],
            'script': script,
            'social_post': social_post,
            'motion_script': motion_script,
            'video_caption': video_caption,
            'episode_title': episode_title,
            'news_count': len(news),
            'market_data': market_data,
            'top_articles': news[:3]
        }

    def _generate_wednesday(self, style_key):
        news = self._get_high_quality_news_timeframe(days_back=2, limit=10)
        movers = self._get_recent_movers()
        script, social_post, motion_script, video_caption, episode_title = self._generate_content_with_style(
            news, "Wednesday", "Mid-week market analysis", style_key
        )
        return {
            'day': 'Wednesday',
            'type': 'Mid-Week Analysis',
            'style': self.style_guide[style_key]['name'],
            'script': script,
            'social_post': social_post,
            'motion_script': motion_script,
            'video_caption': video_caption,
            'episode_title': episode_title,
            'news_count': len(news),
            'top_movers': movers,
            'top_articles': news[:3]
        }

    def _generate_friday(self, style_key):
        news = self._get_high_quality_news_timeframe(days_back=5, limit=12)
        weekly_summary = self._get_weekly_summary()
        script, social_post, motion_script, video_caption, episode_title = self._generate_content_with_style(
            news, "Friday", "Weekly market wrap-up", style_key
        )
        return {
            'day': 'Friday',
            'type': 'Weekly Market Wrap',
            'style': self.style_guide[style_key]['name'],
            'script': script,
            'social_post': social_post,
            'motion_script': motion_script,
            'video_caption': video_caption,
            'episode_title': episode_title,
            'news_count': len(news),
            'weekly_summary': weekly_summary,
            'top_articles': news[:3]
        }

    def _generate_generic(self, style_key):
        news = self._get_high_quality_news(limit=8)
        market_data = self._get_market_snapshot()
        script, social_post, motion_script, video_caption, episode_title = self._generate_content_with_style(
            news, datetime.now().strftime('%A'), "Daily market update", style_key
        )
        return {
            'day': datetime.now().strftime('%A'),
            'type': 'Daily Market Update',
            'style': self.style_guide[style_key]['name'],
            'script': script,
            'social_post': social_post,
            'motion_script': motion_script,
            'video_caption': video_caption,
            'episode_title': episode_title,
            'news_count': len(news),
            'market_data': market_data,
            'top_articles': news[:3]
        }

    # ===== Headlines Section - FIXED =====
    def get_major_headlines(self, limit=15) -> List[Dict[str, Any]]:
        """Get major market headlines with improved Gold/Bitcoin filtering"""
        print("📰 Fetching major market headlines...")
        
        # Get guaranteed Gold/Bitcoin headlines (quality focused)
        guaranteed_headlines = self._get_guaranteed_gold_bitcoin_headlines()
        
        # Get regular market headlines
        regular_headlines = self._get_regular_headlines(limit - len(guaranteed_headlines))
        
        # Combine and remove duplicates
        all_headlines = guaranteed_headlines + regular_headlines
        final_headlines = self._remove_duplicate_headlines(all_headlines)
        
        # Sort by priority (market-moving news first)
        final_headlines.sort(key=lambda x: self._get_priority_score(x), reverse=True)
        
        print(f"📊 Found {len(final_headlines)} major headlines ({len(guaranteed_headlines)} guaranteed Gold/Bitcoin)")
        return final_headlines[:limit]
    
    def _get_guaranteed_gold_bitcoin_headlines(self, limit=2) -> List[Dict[str, Any]]:
        """IMPROVED: Fetch exactly 2 quality Gold and Bitcoin market news"""
        guaranteed = []
        
        time_ranges = [
            (0, 1),   # Today
            (1, 2),   # Yesterday  
            (2, 4),   # 2-4 days ago
            (4, 7)    # 4-7 days ago
        ]
        
        for days_back_start, days_back_end in time_ranges:
            if len(guaranteed) >= limit:
                break
                
            headlines = self._get_headlines_timeframe(days_back_start, days_back_end, limit=100)
            
            # Look for QUALITY Gold commodity news (if we don't have one)
            gold_count = sum(1 for h in guaranteed if self._is_quality_gold_commodity_news(h))
            if gold_count == 0:
                for headline in headlines:
                    if (self._is_quality_gold_commodity_news(headline) and 
                        self._is_quality_headline(headline)):
                        guaranteed.append(headline)
                        print(f"   🥇 Found quality Gold commodity news from {days_back_start}-{days_back_end} days ago")
                        break
            
            # Look for QUALITY Bitcoin/Crypto market news (if we don't have one)
            bitcoin_count = sum(1 for h in guaranteed if self._is_quality_crypto_market_news(h))
            if bitcoin_count == 0 and len(guaranteed) < limit:
                for headline in headlines:
                    if (self._is_quality_crypto_market_news(headline) and 
                        self._is_quality_headline(headline) and
                        not any(self._headlines_similar(headline, existing) for existing in guaranteed)):
                        guaranteed.append(headline)
                        print(f"   ₿ Found quality Bitcoin/Crypto market news from {days_back_start}-{days_back_end} days ago")
                        break
        
        return guaranteed[:limit]
    
    def _is_quality_gold_commodity_news(self, article) -> bool:
        """FIXED: Check for actual gold commodity market news, not company news"""
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        # STRICT EXCLUSION of company-specific news
        company_exclusions = [
            # Focus only on the most spammy corporate actions
            'announces dividend', 'stock split', 'reverse split', 'ipo',
            'if you invested', 'you would have', 'outperformed', 
            
            # Keep specific miners if you want, but consider removing them
            # 'kinross', 'newmont', 'barrick', 
            
            # VERY IMPORTANT: Remove this as it filters out analyst reports
            # 'goldman sachs', 'goldman', 'gs group', 'investment bank'
        ]
        
        if any(term in title or term in summary for term in company_exclusions):
            return False
        
        # POSITIVE INDICATORS for gold commodity news
        gold_commodity_terms = [
            'gold price', 'gold prices', 'gold rally', 'gold surge', 'gold falls',
            'gold futures', 'spot gold', 'gold market', 'gold trading',
            'gold demand', 'gold supply', 'bullion', 'precious metals',
            'gold etf rally', 'gold market outlook', 'gold commodity',
            'central bank gold', 'inflation gold', 'safe haven gold'
        ]
        
        # Must have gold + market context
        has_gold = 'gold' in title or 'gold' in summary
        has_market_context = any(term in title or term in summary for term in gold_commodity_terms)
        
        return has_gold and has_market_context
    
    def _is_quality_crypto_market_news(self, article) -> bool:
        """FIXED: Check for quality crypto market news, not corporate filings"""
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        # Must contain crypto terms
        crypto_terms = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency', 'dogecoin', 'doge']
        has_crypto = any(term in title for term in crypto_terms)
        
        if not has_crypto:
            return False
        
        # EXCLUDE corporate/company news about crypto companies
        corporate_exclusions = [
            'stock split', 'reverse split', 'announces', 'reports earnings',
            'ipo', 'share price', 'stock option', 'dividend', 'sec filing',
            'holding inc', 'technology holding', 'corporation announces'
        ]
        
        if any(term in title for term in corporate_exclusions):
            return False
        
        # INCLUDE market-focused crypto news
        market_indicators = [
            'price', 'rises', 'falls', 'rally', 'surge', 'drops', 'trading',
            'market', 'whale', 'etf', 'adoption', 'regulation', 'sec approval',
            'institutional', 'treasury', 'reserves', 'demand', 'supply'
        ]
        
        has_market_focus = any(term in title or term in summary for term in market_indicators)
        return has_market_focus
    
    def _get_regular_headlines(self, remaining_limit) -> List[Dict[str, Any]]:
        """Get regular market headlines with improved filtering"""
        if remaining_limit <= 0:
            return []
        
        time_from = (datetime.now() - timedelta(hours=18)).strftime('%Y%m%dT%H%M')
            
        params = {
            'function': 'NEWS_SENTIMENT',
            'apikey': self.api_key,
            'limit': 200,  # Get more to filter better
            'sort': 'LATEST'
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            self.call_count += 1
            
            if response.status_code == 200:
                data = response.json()
                
                if 'feed' in data:
                    raw_articles = data['feed']
                    
                    # Filter for QUALITY major headlines only
                    major_headlines = []
                    for article in raw_articles:
                        if self._is_quality_major_headline(article):
                            normalized = self._normalize_article(article)
                            major_headlines.append(normalized)
                    
                    # Sort by priority
                    major_headlines.sort(key=lambda x: self._get_priority_score(x), reverse=True)
                    
                    return major_headlines[:remaining_limit]
                    
        except Exception as e:
            print(f"❌ Error getting regular headlines: {e}")
        
        return []
    
    def _is_quality_major_headline(self, article) -> bool:
        """IMPROVED: Strict filtering for quality market headlines only"""
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        source = article.get('source', '').lower()
        
        # STRICT EXCLUSIONS - no exceptions
        strict_exclusions = [
            # Legal/spam content
            'shareholder alert', 'class action', 'lawsuit', 'attorney', 'investigation',
            'legal notice', 'court', 'settlement', 'plaintiff', 'damages', 'reminds investors',
            'law firm', 'securities fraud', 'kahn swick', 'losses in excess',
            
            # Corporate filing spam
            'announces grant', 'stock options', 'reverse stock split', 'stock split',
            'dividend announcement', 'board of directors', 'executive appointment',
            'quarterly dividend', 'special dividend', 
            
            # Retrospective/analysis spam
            'if you invested', 'you would have', 'outperformed', '5 years ago',
            'strong buy', 'trending stocks', 'stocks for your', 'zacks rank',
            
            # Generic listicle content
            '3 stocks', '5 stocks', 'top stocks', 'stocks to buy', 'stocks to watch'
        ]
        
        if any(term in title for term in strict_exclusions):
            return False
        
        # QUALITY INDICATORS - must have at least one
        quality_indicators = [
            # Major market events
            'fed', 'federal reserve', 'interest rate', 'inflation', 'gdp', 'cpi',
            'jobs report', 'unemployment', 'economic data', 'retail sales',
            
            # Market movements
            'market rally', 'market surge', 'market falls', 'record high', 'all-time high',
            'correction', 'volatility', 'dow', 'nasdaq', 's&p 500', 'index',
            
            # Major earnings (only big companies)
            'earnings beat', 'earnings miss', 'quarterly results', 'revenue',
            
            # Sector news
            'energy sector', 'tech sector', 'financial sector', 'banking',
            'oil prices', 'crude oil', 'natural gas', 'energy',
            
            # Currency/commodities (already handled in guaranteed section)
            'dollar', 'treasury', 'bonds', 'yield curve'
        ]
        
        has_quality_content = any(term in title or term in summary for term in quality_indicators)
        
        # Major company earnings are OK if from reputable sources
        major_companies = [
            'apple', 'microsoft', 'google', 'amazon', 'tesla', 'nvidia',
            'meta', 'netflix', 'adobe', 'oracle', 'salesforce'
        ]
        
        is_major_company_news = any(company in title for company in major_companies)
        is_reputable_source = any(src in source for src in ['cnbc', 'reuters', 'bloomberg', 'wsj', 'marketwatch'])
        
        # Title quality checks
        title_length_ok = 30 <= len(title) <= 120
        not_all_caps = not title.isupper()
        
        return ((has_quality_content or (is_major_company_news and is_reputable_source)) 
                and title_length_ok and not_all_caps)
    
    def _get_priority_score(self, article) -> int:
        """IMPROVED: Better priority scoring for market-relevant news"""
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        score = 0
        
        # HIGHEST PRIORITY: Quality Gold and Bitcoin market news (150+)
        if self._is_quality_gold_commodity_news(article):
            score += 150
        elif self._is_quality_crypto_market_news(article):
            score += 140
        
        forex_critical = [
            'federal reserve', 'fed meeting', 'fomc', 'interest rate', 'monetary policy',
            'ecb', 'boe', 'boj', 'snb', 'rba', 'boc', # International Central Banks
            'cpi', 'inflation data', 'non-farm payrolls', 'nfp', # Top-tier data
            'jobs report', 'gdp', 'unemployment', 'hawkish', 'dovish'
        ]
        if any(term in title for term in forex_critical):
            score += 160

        # GEOPOLITICAL EVENTS (140+)
        # A crucial new category for major market-moving news.
        geopolitical_events = [
            'geopolitical', 'trade war', 'tariffs', 'sanctions', 'election', 
            'summit', 'opec', 'brexit'
        ]
        if any(term in title for term in geopolitical_events):
            score += 140

        # FOREX & BOND MARKET MOVEMENT (120+)
        # Specific terms for currency and bond market volatility.
        forex_market_events = [
            'dollar', 'euro', 'yen', 'pound', 'currency', 'risk-on', 'risk-off', 
            'safe-haven', 'bond yields', 'yield curve', 'treasury'
        ]
        if any(term in title for term in forex_market_events):
            score += 120
            
        # MEDIUM-HIGH: General Stock Market Movements (80+)
        # Your existing list, still relevant for overall sentiment.
        market_events = [
            'record high', 'all-time high', 'market rally', 'market surge',
            'dow hits', 'nasdaq reaches', 's&p 500', 'correction', 'sell-off'
        ]
        if any(term in title for term in market_events):
            score += 80
        
        # MEDIUM: Sector/Commodity News (60+)
        # Your existing list, works well.
        sector_news = [
            'oil prices', 'crude oil', 'energy sector', 'tech sector',
            'banking sector', 'financials'
        ]
        if any(term in title for term in sector_news):
            score += 60
        
        # MEDIUM-LOW: Major Company Earnings (40+)
        # Your existing list for major tech earnings.
        if 'earnings' in title and any(company in title for company in [
            'apple', 'microsoft', 'google', 'amazon', 'tesla', 'nvidia'
        ]):
            score += 40
        
        # BONUS: Strong sentiment indicates market impact
        sentiment_score = abs(article.get('sentiment_score', 0))
        if sentiment_score > 0.7:
            score += 20
        elif sentiment_score > 0.4:
            score += 10
        
        # BONUS: Multiple tickers (broader market impact)
        ticker_count = len(article.get('tickers', []))
        if ticker_count >= 3:
            score += 15
        elif ticker_count >= 1:
            score += 5
        
        return score

    def _get_headlines_timeframe(self, days_back_start, days_back_end, limit=50) -> List[Dict[str, Any]]:
        """Get headlines from a specific timeframe"""
        end_date = datetime.now() - timedelta(days=days_back_start)
        start_date = datetime.now() - timedelta(days=days_back_end)
        
        params = {
            'function': 'NEWS_SENTIMENT',
            'apikey': self.api_key,
            'limit': limit,
            'time_from': start_date.strftime('%Y%m%dT0000'),
            'time_to': end_date.strftime('%Y%m%dT2359'),
            'sort': 'LATEST'
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            self.call_count += 1
            
            if response.status_code == 200:
                data = response.json()
                if 'feed' in data:
                    return [self._normalize_article(a) for a in data['feed']]
        except Exception as e:
            print(f"❌ Error getting timeframe headlines: {e}")
        
        return []
    
    def _is_quality_headline(self, article) -> bool:
        """Basic quality check for headlines"""
        title = article.get('title', '')
        
        # Basic quality checks
        title_length_ok = 25 <= len(title) <= 150
        not_all_caps = not title.isupper()
        not_spam = not any(spam in title.lower() for spam in ['alert', 'reminder', 'deadline'])
        
        return title_length_ok and not_all_caps and not_spam
    
    def _remove_duplicate_headlines(self, headlines) -> List[Dict[str, Any]]:
        """Remove duplicate headlines based on title similarity"""
        seen_titles = set()
        unique_headlines = []
        
        for headline in headlines:
            title_key = headline.get('title', '').lower()[:60]  # First 60 chars as key
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_headlines.append(headline)
        
        return unique_headlines

    def display_headlines(self) -> None:
        """Display major headlines in a clean format"""
        headlines = self.get_major_headlines()
        
        if not headlines:
            print("❌ No major headlines available")
            return
        
        print("\n" + "="*80)
        print("📰 MAJOR MARKET HEADLINES TODAY")
        print("="*80)
        
        for i, headline in enumerate(headlines, 1):
            # Format timestamp and check if it's from previous days
            time_pub = headline.get('time_published', '')
            age_indicator = ""
            
            if time_pub and len(time_pub) >= 8:
                try:
                    pub_date = datetime.strptime(time_pub[:8], '%Y%m%d')
                    today = datetime.now().date()
                    pub_date_only = pub_date.date()
                    
                    days_ago = (today - pub_date_only).days
                    
                    if days_ago == 0:
                        formatted_time = f"{time_pub[4:6]}/{time_pub[6:8]} {time_pub[9:11]}:{time_pub[11:13]}"
                    elif days_ago == 1:
                        formatted_time = f"Yesterday {time_pub[9:11]}:{time_pub[11:13]}"
                        age_indicator = " 📅"
                    elif days_ago <= 7:
                        formatted_time = f"{days_ago}d ago {time_pub[9:11]}:{time_pub[11:13]}"
                        age_indicator = " 📅"
                    else:
                        formatted_time = f"{time_pub[4:6]}/{time_pub[6:8]} (older)"
                        age_indicator = " 📅"
                        
                except:
                    formatted_time = "Recent"
            else:
                formatted_time = "Recent"
            
            # Format tickers
            tickers_display = ""
            if headline.get('tickers'):
                tickers_display = f" [{', '.join(headline['tickers'][:3])}]"
            
            # IMPROVED sentiment icon assignment
            if self._is_quality_gold_commodity_news(headline):
                sentiment_icon = "🥇"
            elif self._is_quality_crypto_market_news(headline):
                sentiment_icon = "₿"
            elif headline.get('sentiment') == 'bullish':
                sentiment_icon = "📈"
            elif headline.get('sentiment') == 'bearish':
                sentiment_icon = "📉"
            else:
                sentiment_icon = "📊"
            
            print(f"\n{i:2d}. {headline['title']}{tickers_display}{age_indicator}")
            print(f"    {sentiment_icon} {headline.get('sentiment', 'neutral').title()} | {headline['source']} | {formatted_time}")
            
            if headline.get('summary') and len(headline['summary']) > 50:
                summary_short = headline['summary'][:120] + "..." if len(headline['summary']) > 120 else headline['summary']
                print(f"    {summary_short}")
        
        print(f"\n📊 Total headlines: {len(headlines)}")
        print("🥇 Gold Commodity | ₿ Bitcoin/Crypto Market | 📅 Previous days")
        print("="*80)

    # ===== Content Generation with Style System =====
    def _generate_content_with_style(self, news: List[Dict], day: str, theme: str, style_key: str) -> Tuple[str, str, str, str, str]:
        """Generate professional content using specified style guide"""
        
        style_config = self.style_guide[style_key]
        target_seconds = style_config["target_seconds"]
        
        if not news:
            return self._create_fallback_content_with_style(news, day, style_key)

        # Prepare context with top stories
        top_stories = []
        for i, article in enumerate(news[:5], 1):
            tickers_str = f" (${', '.join(article['tickers'][:2])})" if article.get('tickers') else ""
            top_stories.append(f"{i}. {article['title']}{tickers_str}")
            top_stories.append(f"   Sentiment: {article['sentiment']} ({article['sentiment_score']:.2f})")
            if article.get('summary'):
                top_stories.append(f"   Summary: {article['summary'][:100]}...")
        
        context = f"Date: {datetime.now().strftime('%B %d, %Y')}\nTop Stories Available:\n" + "\n".join(top_stories)
        
        # Style-specific system prompt
        system_prompt = f"""You are an expert global market analyst creating content for a sophisticated financial audience. Your primary goal is to identify and report on the most impactful news driving global markets.

PRIORITIZATION HIERARCHY:
1.  **Top Priority:** Major economic data releases (Inflation/CPI, GDP, Jobs/NFP) from G7 nations.
2.  **High Priority:** Central bank announcements (Fed, ECB, BoE, BoJ) and significant geopolitical events.
3.  **Medium Priority:** Major M&A deals and significant, confirmed corporate news.
4.  **Lower Priority:** Market speculation, rumors, and analyst commentary.

Your task is to select the top 3 most important stories from the provided context based on this hierarchy and build the script around them.


SELECTED STYLE: {style_config['name']}
DESCRIPTION: {style_config['description']}
TONE: {style_config['tone']}
PACING: {style_config['pacing']}
TARGET LENGTH: {target_seconds} seconds

VOICE-FRIENDLY RULES:
- NEVER write ticker symbols that will be read aloud (e.g., $AAPL, FOREX:USD, CRYPTO:BTC)
- Use company/asset names: "Apple", "US Dollar", "Bitcoin"
- For unknown tickers, use generic terms: "the company", "related stocks", "cryptocurrency markets"
- Only use ticker symbols in parentheses if they add clarity

CRITICAL: Return ONLY valid JSON with script, social, motion, caption, and title keys."""

        # Style-specific user prompt
        user_prompt = self._build_style_specific_prompt(style_key, context, target_seconds, theme)
        
        try:
            print(f"🤖 Generating {style_config['name']} content with GPT-4o...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=1200,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            full_output = response.choices[0].message.content.strip()
            
            try:
                parsed = json.loads(full_output)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                return self._create_fallback_content_with_style(news, day, style_key)

            script = parsed.get("script", "").strip()
            social = parsed.get("social", "").strip()
            motion = parsed.get("motion", "").strip()
            caption = parsed.get("caption", "").strip()
            title = parsed.get("title", "").strip()

            if self._validate_professional_content(script, social, motion, caption, target_seconds):
                print(f"✅ Success with {style_config['name']} style")
                return script, social, motion, caption, title
            else:
                print(f"⚠️ Content quality check failed, using fallback")
                return self._create_fallback_content_with_style(news, day, style_key)

        except Exception as e:
            print(f"❌ Error generating content: {str(e)}")
            return self._create_fallback_content_with_style(news, day, style_key)

    def _build_style_specific_prompt(self, style_key: str, context: str, target_seconds: int, theme: str, weekly_context: Dict = None) -> str:
        """Build style-specific prompts for different news styles"""
        
        current_date = datetime.now().strftime('%B %d')
        
        # Base requirements for all styles
        base_requirements = f"""
    CONTEXT:
    {context}

    SCRIPT REQUIREMENTS:
    - {target_seconds} seconds when spoken at news pace (~{target_seconds * 2.5} words)
    - EXACTLY 3 STORIES with varied, natural transitions
    - VOICE-FRIENDLY: Use company names, not ticker symbols
    - EXCLUDE: Legal notices, shareholder alerts, class action lawsuits
    - FOCUS: Market movements, earnings, economic policy, sector trends
    - TARGET LENGTH: Aim for {target_seconds * 2.5} words minimum

    SOCIAL POST REQUIREMENTS:
    - 60-90 words, professional LinkedIn/X audience
    - Strong opening, 2-3 bullet points, concluding thought
    - Include 2-3 relevant tickers or figures
    - NO emojis, 3-4 hashtags like #MarketUpdate #Investing

    MOTION SCRIPT (300 chars max):
    - Professional body language directions
    - Opening stance, gestures, transitions, closing

    VIDEO CAPTION (60-80 chars):
    - Professional video title with date and key topics

    THEME: {theme}

    Return JSON format:
    {{
    "script": "script here",
    "social": "social post here", 
    "motion": "motion directions here",
    "caption": "video caption here",
    "title": "episode title here"
    }}
    """

        # Style-specific examples and instructions
        if style_key == "classic_daily":
            return f"""Create a 'Classic Daily Brief' script that is punchy, insightful, and tells a story about the market today.

    CRITICAL INSTRUCTIONS:
    1.  **Find the Narrative:** Don't just list news. Find the connecting theme. Is today about inflation fears? A tech rebound? Geopolitical tension? State this theme upfront.
    2.  **Answer "So What?":** For each story, immediately explain its impact. Why should a regular investor care? Use phrases that connect news to personal impact (e.g., "which could mean...", "the big risk here is...").
    3.  **Use a Conversational Hook:** Start with a question or a bold statement, not just "Here's your update."

    TEMPLATE / STRUCTURE:
    "[Engaging Hook related to the day's theme]. Let's break down what's really moving the markets.
    First up, the biggest story: [STORY 1, explaining its direct market impact].
    Next, keep an eye on this: [STORY 2, explaining what it signals for the future].
    And finally, a move under the radar: [STORY 3, and why it matters].
    So, the big picture today is [reiterate the main theme]. That's your rundown — see you tomorrow!"

    EXAMPLE STYLE (This is the tone to aim for):
    "So, is the market finally getting nervous about inflation? Let's break down what's really moving the markets.
    First up, the biggest story: The Fed just signaled that rate cuts might be further away than we thought, which sent a shockwave through the tech sector.
    Next, keep an eye on this: Oil prices are spiking above $95 a barrel. For you, that could mean more pain at the gas pump very soon.
    And finally, a move under the radar: A major corporate Bitcoin purchase just hit the wires, showing big institutions are still betting on crypto long-term.
    So, the big picture today is caution. The market is weighing inflation risks against corporate confidence. That's your rundown — see you tomorrow!"

    KEY PHRASES TO USE:
    - "Let's break down what's really moving the markets."
    - "The big picture today is..."
    - "For you, that could mean..."
    - "Keep an eye on this..."

    {base_requirements}"""

        elif style_key == "breaking_alert":
            return f"""Create a Breaking News Alert script following this URGENT template:

    TEMPLATE:
    "BREAKING NEWS for your market update. First, [URGENT STORY with immediate impact]. 
    JUST IN — [SECOND BREAKING STORY with dramatic element]. And finally — [THIRD STORY with critical level]. 
    All eyes are on what happens next. That's your breaking update — more as it develops."

    EXAMPLE STYLE:
    "BREAKING NEWS for your market update. First, the Fed just signaled a surprise policy shift, sending tech stocks tumbling. 
    JUST IN — NVIDIA shares are halted pending a major announcement, sparking sector-wide volatility. 
    And finally — Bitcoin has just breached a critical support level at $115,000. 
    All eyes are on what happens next. That's your breaking update — more as it develops."

    KEY PHRASES TO USE:
    - "BREAKING NEWS"
    - "JUST IN"
    - "sparking sector-wide volatility"
    - "critical support/resistance level"
    - "All eyes are on what happens next"

    {base_requirements}"""

        elif style_key == "weekly_deep":
            # Enhanced weekly deep dive with actual weekly context
            weekly_info = ""
            if weekly_context:
                themes = weekly_context.get('themes', {})
                summary = weekly_context.get('summary', {})
                
                if themes.get('primary_theme'):
                    weekly_info += f"WEEKLY THEME: {themes['primary_theme']}\n"
                
                if summary.get('weekly_change'):
                    weekly_info += f"WEEKLY PERFORMANCE: S&P 500 {summary['weekly_change']}\n"
                
                if themes.get('sector_leaders'):
                    leaders = [sector.title() for sector, count in themes['sector_leaders'][:2]]
                    weekly_info += f"LEADING SECTORS: {', '.join(leaders)}\n"
                
                if themes.get('top_5_stories'):
                    weekly_info += "TOP 5 WEEKLY STORIES PROVIDED IN CONTEXT\n"
            
            return f"""Create a TRUE Weekly Deep Dive script following this ANALYTICAL template:

    IMPORTANT: This is a WEEKLY ANALYSIS covering Monday through Friday, NOT daily news.

    TEMPLATE:
    "Here is your weekly market analysis. The primary catalyst this week was [WEEKLY THEME from context], which [WEEKLY MARKET IMPACT and performance]. 
    In corporate developments, [MAJOR CORPORATE STORY from the week with broader implications]. 
    Looking ahead, the key data point will be [UPCOMING WEEK'S FOCUS]. The street is anticipating [NEXT WEEK'S EXPECTATION]. 
    This has been your weekly market analysis."

    WEEKLY CONTEXT PROVIDED:
    {weekly_info}

    WEEKLY LANGUAGE REQUIREMENTS:
    - Use "this week" not "today" 
    - Reference week-long trends: "throughout the week", "over five trading days"
    - Mention weekly performance: "the S&P gained X% for the week"
    - Use past tense for the week's events: "dominated this week", "emerged as"
    - Forward-looking: "heading into next week", "the week ahead"

    EXAMPLE WEEKLY STYLE:
    "Here is your weekly market analysis. The primary catalyst this week was Federal Reserve uncertainty, which created sustained volatility across all major indices with the S&P 500 gaining 1.8% for the week despite Tuesday's selloff.
    In corporate developments, the energy sector dominated headlines with three major oil companies reporting record quarterly profits, underscoring the sector's resilience amid geopolitical tensions. 
    Looking ahead, the key data point will be next week's inflation data release. The street is anticipating this could determine the Fed's December policy stance.
    This has been your weekly market analysis."

    KEY WEEKLY PHRASES TO USE:
    - "The primary catalyst this week was..."
    - "throughout the trading week"
    - "dominated headlines this week"
    - "over the five-day period"
    - "heading into next week"
    - "This has been your weekly market analysis"

    {base_requirements}"""

        elif style_key == "market_pulse":
            return f"""Create a Market Pulse script following this ENERGETIC template:

    TEMPLATE:
    "Time for your market pulse check! [SECTOR/ASSET] is [ACTION VERB] today on [CATALYST]. 
    Meanwhile, [CONTRASTING STORY] as traders [REACTION]. The mood on the street? [SENTIMENT]. 
    Here's what's driving the action: [KEY FACTORS]. Your market pulse — [CURRENT STATE] with [OUTLOOK]. Keep watching!"

    KEY ACTION VERBS TO USE:
    - surging, plunging, rallying, retreating, soaring, tumbling, spiking, diving

    KEY PHRASES TO USE:
    - "Time for your market pulse check!"
    - "Meanwhile"
    - "The mood on the street?"
    - "Here's what's driving the action:"
    - "Your market pulse —"
    - "Keep watching!"

    TONE: Energetic, rhythmic, engaging with momentum-focused language

    {base_requirements}"""

        elif style_key == "forex_briefing":
            return f"""Create a Forex Daily Briefing script focusing on actual currency market impact:

        CRITICAL INSTRUCTIONS:
        - Analyze the provided news context for stories that affect major currencies
        - Focus ONLY on G7 currencies: USD, EUR, JPY, GBP, CAD, AUD, CHF
        - If economic data is mentioned, explain its currency impact
        - If no forex-relevant news exists, create a brief summary acknowledging limited forex developments
        - Use specific currency pair names (EUR/USD, GBP/JPY, etc.) only when justified by the news
        - Do NOT use placeholder examples or generic statements

        TEMPLATE STRUCTURE (adapt based on actual news):
        "Here is your forex daily briefing for {current_date}. [Analyze actual news for currency impacts]
        [Connect specific news to currency movements]
        [Mention any relevant central bank developments]
        Looking ahead, [mention actual upcoming events if any]. That's your forex briefing — trade safe."

        AVOID:
        - Generic examples like "testing 1.10 resistance"
        - Placeholder currency pairs when news doesn't support them
        - Making up economic data releases not mentioned in context

        {base_requirements}"""

        elif style_key == "strategic_outlook":
            return f"""Create a Strategic Outlook script following this INSTITUTIONAL template:

    TEMPLATE:
    "Your strategic market briefing: [MACRO CONTEXT] is reshaping [MARKET/SECTOR] dynamics. 
    From a strategic standpoint, [INSTITUTIONAL PERSPECTIVE with risk/reward analysis]. 
    On the tactical side, watch for [SPECIFIC LEVELS/EVENTS] as potential inflection points. 
    Our take: [STRATEGIC RECOMMENDATION] while monitoring [KEY RISKS]. Strategic briefing complete — position accordingly."

    KEY INSTITUTIONAL PHRASES TO USE:
    - "Your strategic market briefing:"
    - "From a strategic standpoint..."
    - "The risk-reward equation suggests..."
    - "On the tactical side..."
    - "Our take:"
    - "as potential inflection points"
    - "Strategic briefing complete — position accordingly"

    TONE: Advisory, measured, institutional with strategic perspective

    {base_requirements}"""
        
        else:
            # Handle unknown style keys gracefully
            return base_requirements

    def _create_fallback_content_with_style(self, news: List[Dict], day: str, style_key: str) -> Tuple[str, str, str, str, str]:
        """Create style-specific fallback content"""
        style_config = self.style_guide[style_key]
        current_date = datetime.now().strftime('%B %d')
        
        # Style-specific fallback scripts
        if style_key == "breaking_alert":
            script = f"BREAKING NEWS for your market update. First, markets are showing heightened volatility as traders react to developing economic data. JUST IN — major indices are experiencing unusual trading patterns amid uncertainty. And finally — key support levels are being tested across multiple sectors. All eyes are on what happens next. That's your breaking update — more as it develops."
            
        elif style_key == "weekly_deep":
            script = f"Here is your weekly market analysis. The primary catalyst this week was mixed economic signals, which created uncertainty in equity markets. In corporate developments, several major companies are navigating regulatory changes that could impact their strategic direction. Looking ahead, the key data point will be upcoming Federal Reserve commentary. The street is anticipating this will provide clarity on monetary policy. This has been your weekly market analysis."
            
        elif style_key == "market_pulse":
            script = f"Time for your market pulse check! Markets are consolidating today on mixed economic signals. Meanwhile, sector rotation continues as traders position for upcoming data releases. The mood on the street? Cautiously optimistic with selective buying. Here's what's driving the action: economic uncertainty balanced against corporate resilience. Your market pulse — steady with defensive positioning. Keep watching!"
            
        elif style_key == "strategic_outlook":
            script = f"Your strategic market briefing: evolving economic conditions are reshaping portfolio allocation dynamics. From a strategic standpoint, the risk-reward equation suggests maintaining balanced exposure while monitoring key indicators. On the tactical side, watch for upcoming economic data as potential inflection points. Our take: maintain defensive positioning while monitoring emerging opportunities. Strategic briefing complete — position accordingly."
            
        else:  # classic_daily
            script = f"Here's your market update for {current_date}. First up — markets are showing mixed signals as investors digest recent economic data. Next — the Federal Reserve continues monitoring key inflation indicators. And finally — several major sectors are experiencing rotational trading patterns. That's your {current_date} rundown — see you tomorrow!"
        
        # Common elements for all styles
        social = f"Market analysis for {current_date}: Mixed signals prevail as investors weigh economic data against corporate fundamentals. Key themes include Federal Reserve policy outlook and sector rotation dynamics. Strategic positioning remains focused on quality names with strong fundamentals. #MarketUpdate #Investing #FinancialNews #Strategy"
        
        motion = f"Professional opening with {style_config['tone']} delivery. Emphasize key transitions matching {style_config['pacing']} pace. Maintain authoritative posture throughout. End with confident, style-appropriate closing gesture."
        
        caption = f"{style_config['name']} - {current_date} | Markets, Fed & Strategy"
        title = f"{style_config['name']} - {current_date} | Economic Data and Market Analysis"
        
        return script, social, motion, caption, title

    def _validate_professional_content(self, script: str, social: str, motion: str, caption: str, target_seconds: int) -> bool:
        """Validate generated content meets professional standards"""
        
        if len(script) < 100:
            print("Validation failed: Script too short.")
            return False
        
        if len(social) > 800 or len(social) < 150:
            print(f"Validation failed: Social post length is {len(social)}, outside 150-800 range.")
            return False
        
        if len(motion) > 350 or len(motion) < 50:
            print("Validation failed: Motion script length out of range.")
            return False
        
        if len(caption) > 100 or len(caption) < 20:
            print("Validation failed: Caption length out of range.")
            return False
        
        return True

    # ===== News Fetch =====
    def _get_high_quality_news(self, limit=8):
        params = {
            'function': 'NEWS_SENTIMENT',
            'apikey': self.api_key,
            'limit': 100,
            'sort': 'LATEST'
        }
        try:
            print(f"🔍 Calling Alpha Vantage API...")
            response = requests.get(self.base_url, params=params, timeout=30)
            self.call_count += 1
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 API Response Keys: {list(data.keys())}")
                
                if 'feed' in data:
                    raw_articles = data['feed']
                    print(f"📰 Raw articles found: {len(raw_articles)}")
                    
                    if self.debug_mode and raw_articles:
                        print(f"\n🔍 First article sample:")
                        print(f"Title: {raw_articles[0].get('title', 'N/A')}")
                        print(f"Source: {raw_articles[0].get('source', 'N/A')}")
                        print(f"Summary: {raw_articles[0].get('summary', 'N/A')[:100]}...")
                    
                    # IMPROVED filtering - use quality check instead of basic
                    filtered_articles = [self._normalize_article(a) for a in raw_articles 
                                       if self._is_quality_financial_content(a)]
                    
                    if self.debug_mode:
                        print(f"📋 Articles after quality filtering: {len(filtered_articles)}")
                        if filtered_articles:
                            print("\n✅ Sample filtered articles:")
                            for i, article in enumerate(filtered_articles[:3]):
                                print(f"{i+1}. {article['title'][:80]}...")
                                print(f"   Source: {article['source']}")
                    
                    return filtered_articles[:limit]
                else:
                    print(f"❌ No 'feed' key in response. Available keys: {list(data.keys())}")
                    if 'Error Message' in data:
                        print(f"❌ API Error: {data['Error Message']}")
                    if 'Note' in data:
                        print(f"ℹ️ API Note: {data['Note']}")
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"Response text: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error getting news: {e}")
        return []

    def _get_high_quality_news_timeframe(self, days_back, limit):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        params = {
            'function': 'NEWS_SENTIMENT',
            'apikey': self.api_key,
            'limit': 100,
            'time_from': start_date.strftime('%Y%m%dT0000'),
            'time_to': end_date.strftime('%Y%m%dT2359')
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            self.call_count += 1
            if response.status_code == 200:
                data = response.json()
                if 'feed' in data:
                    raw_articles = data['feed']
                    filtered_articles = [self._normalize_article(a) for a in raw_articles 
                                       if self._is_quality_financial_content(a)]
                    return filtered_articles[:limit]
        except Exception as e:
            print(f"❌ Error getting timeframe news: {e}")
        return []
    
    def _is_quality_financial_content(self, article):
        """IMPROVED: Enhanced check for quality financial content with stricter filtering"""
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        source = article.get('source', '').lower()
        
        # STRICT EXCLUSIONS - same as headline filtering
        strict_exclusions = [
            # Legal/spam content
            'shareholder alert', 'class action', 'lawsuit', 'attorney', 'investigation',
            'legal notice', 'court', 'settlement', 'plaintiff', 'damages', 'reminds investors',
            'law firm', 'securities fraud', 'kahn swick', 'losses in excess',
            
            # Corporate filing spam
            'announces grant', 'stock options', 'reverse stock split', 'stock split',
            'dividend announcement', 'board of directors', 'executive appointment',
            
            # Retrospective/analysis spam
            'if you invested', 'you would have', 'outperformed', '5 years ago',
            'strong buy', 'trending stocks', 'stocks for your', 'zacks rank',
            
            # Generic content
            '3 stocks', '5 stocks', 'top stocks', 'stocks to buy', 'stocks to watch'
        ]
        
        if any(term in title for term in strict_exclusions):
            return False
        
        # A story is significant if it's about a major company OR a high-impact event.
        is_significant = False
        if any(company in title for company in self.MAJOR_COMPANIES):
            is_significant = True
        if any(keyword in title or keyword in summary for keyword in self.HIGH_IMPACT_KEYWORDS):
            is_significant = True

        # If a story is not about a major name or a major event, we skip it.
        if not is_significant:
            return False
        
        # POSITIVE INDICATORS for quality financial content
        quality_indicators = [
            # Market movements and data
            'earnings', 'revenue', 'profit', 'guidance', 'outlook', 'beats', 'misses',
            'market', 'trading', 'price', 'rally', 'surge', 'falls', 'drops',
            
            # Economic indicators
            'fed', 'federal reserve', 'interest rate', 'inflation', 'gdp', 'employment',
            'economic data', 'consumer confidence', 'retail sales', 'manufacturing',
            
            # Sectors and commodities
            'energy', 'technology', 'healthcare', 'financials', 'oil prices', 'gold',
            'cryptocurrency', 'bitcoin', 'ethereum', 'bonds', 'treasury', 'currency',
            
            # Major market events
            'ipo', 'merger', 'acquisition', 'partnership', 'deal', 'contract'
        ]
        
        # Must have financial indicators AND quality checks
        has_financial_content = any(term in title or term in summary for term in quality_indicators)
        has_tickers = len(article.get('ticker_sentiment', [])) > 0
        
        # Title quality
        title_length_ok = 25 <= len(title) <= 150
        not_all_caps = not title.isupper()
        
        return (has_financial_content or has_tickers) and title_length_ok and not_all_caps

    def _normalize_article(self, article):
        tickers = [item.get('ticker') for item in article.get('ticker_sentiment', []) if item.get('ticker')]
        
        return {
            'title': article.get('title', ''),
            'summary': article.get('summary', ''),
            'source': article.get('source', ''),
            'time_published': article.get('time_published', ''),
            'sentiment': article.get('overall_sentiment_label', 'neutral'),
            'sentiment_score': float(article.get('overall_sentiment_score', 0)),
            'tickers': tickers,
            'url': article.get('url', ''),
            'quality_score': 75
        }

    # ===== Market Data =====
    def _get_market_snapshot(self):
        try:
            import yfinance as yf
            spy = yf.Ticker('SPY')
            hist = spy.history(period="2d")
            if len(hist) >= 2:
                current, previous = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                change_pct = ((current - previous) / previous) * 100
                return {
                    'symbol': 'SPY', 
                    'price': f"${current:.2f}", 
                    'change': f"{change_pct:+.2f}%", 
                    'status': 'connected'
                }
        except ImportError:
            print("⚠️ yfinance not installed. Install with: pip install yfinance")
        except Exception as e:
            print(f"❌ Error getting market snapshot: {e}")
        return {'status': 'error'}

    def _get_recent_movers(self):
        try:
            import yfinance as yf
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
            movers = []
            for symbol in symbols[:4]:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current, previous = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                    change_pct = ((current - previous) / previous) * 100
                    if abs(change_pct) > 1.5:
                        movers.append({
                            'symbol': symbol, 
                            'change': f"{change_pct:+.2f}%", 
                            'price': f"${current:.2f}"
                        })
            return movers
        except Exception as e:
            print(f"❌ Error getting movers: {e}")
            return []

    def _get_weekly_summary(self):
        try:
            import yfinance as yf
            spy = yf.Ticker('SPY')
            hist = spy.history(period="1mo")
            if len(hist) >= 5:
                current, week_ago = hist['Close'].iloc[-1], hist['Close'].iloc[-5]
                weekly_change = ((current - week_ago) / week_ago) * 100
                week_high = hist['High'].tail(5).max()
                week_low = hist['Low'].tail(5).min()
                return {
                    'weekly_change': f"{weekly_change:+.1f}%", 
                    'week_high': f"${week_high:.2f}", 
                    'week_low': f"${week_low:.2f}"
                }
        except Exception as e:
            print(f"❌ Error getting weekly summary: {e}")
        return {}

    # ===== Excel Saving =====
    def save_to_excel(self, content: Dict[str, Any]) -> str:
        """Save content to Excel with style information"""
        filename = "market_content_tracker.xlsx"
        
        try:
            file_exists = os.path.exists(filename)
            
            if file_exists:
                try:
                    existing_df = pd.read_excel(filename, sheet_name='Content_Log')
                    print(f"📄 Updating existing file: {filename}")
                    print(f"📊 Current entries in file: {len(existing_df)}")
                except Exception as e:
                    print(f"⚠️ Could not read existing file ({e}), creating new structure")
                    existing_df = pd.DataFrame(columns=[
                        'Date', 'Time', 'Day', 'Content_Type', 'Style', 'Script', 'Social_Post',
                        'Motion_Script', 'Video_Caption', 'Episode_Title', 'Script_Length', 'Word_Count', 
                        'News_Count', 'Market_Data', 'Quality_Score'
                    ])
            else:
                existing_df = pd.DataFrame(columns=[
                    'Date', 'Time', 'Day', 'Content_Type', 'Style', 'Script', 'Social_Post',
                    'Motion_Script', 'Video_Caption', 'Episode_Title', 'Script_Length', 'Word_Count', 
                    'News_Count', 'Market_Data', 'Quality_Score'
                ])
                print(f"📄 Creating new file: {filename}")
            
            # Prepare new row data
            current_time = datetime.now()
            
            market_data_str = ""
            if content.get('market_data') and content['market_data'].get('status') == 'connected':
                market_data_str = f"SPY: {content['market_data']['price']} ({content['market_data']['change']})"
            
            new_row = {
                'Date': current_time.strftime('%Y-%m-%d'),
                'Time': current_time.strftime('%H:%M:%S'),
                'Day': content['day'],
                'Content_Type': content['type'],
                'Style': content.get('style', 'Classic Daily Brief'),
                'Script': content['script'],
                'Social_Post': content['social_post'],
                'Motion_Script': content.get('motion_script', ''),
                'Video_Caption': content.get('video_caption', ''),
                'Episode_Title': content.get('episode_title', ''),
                'Script_Length': len(content['script']),
                'Word_Count': len(content['script'].split()),
                'News_Count': content.get('news_count', 0),
                'Market_Data': market_data_str,
                'Quality_Score': 'Generated' if content.get('news_count', 0) > 0 else 'Fallback'
            }
            
            new_row_df = pd.DataFrame([new_row])
            new_df = pd.concat([existing_df, new_row_df], ignore_index=True)
            
            print(f"🔍 Adding new row: {new_row['Date']} {new_row['Time']} - {new_row['Day']} ({new_row['Style']})")
            
            # Sort by Date and Time (most recent first)
            new_df['DateTime'] = pd.to_datetime(new_df['Date'] + ' ' + new_df['Time'])
            new_df = new_df.sort_values('DateTime', ascending=False).drop('DateTime', axis=1)
            
            # Save to Excel
            with pd.ExcelWriter(filename, engine='openpyxl', mode='w') as writer:
                new_df.to_excel(writer, sheet_name='Content_Log', index=False, header=True)
                
                # Create summary sheet
                summary_data = pd.DataFrame({
                    'Metric': [
                        'Total Entries', 'Last Updated', 'Most Used Style', 
                        'Average Script Length', 'Total Words Generated'
                    ],
                    'Value': [
                        len(new_df),
                        current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        new_df['Style'].mode().iloc[0] if len(new_df) > 0 else 'None',
                        f"{new_df['Script_Length'].mean():.0f} characters" if len(new_df) > 0 else '0',
                        new_df['Word_Count'].sum() if len(new_df) > 0 else 0
                    ]
                })
                summary_data.to_excel(writer, sheet_name='Summary', index=False)
                
                # Major Headlines tab
                major_headlines = self.get_major_headlines(limit=20)
                if major_headlines:
                    headlines_data = []
                    for i, headline in enumerate(major_headlines, 1):
                        time_pub = headline.get('time_published', '')
                        formatted_time = ""
                        if time_pub and len(time_pub) >= 8:
                            formatted_time = f"{time_pub[4:6]}/{time_pub[6:8]} {time_pub[9:11]}:{time_pub[11:13]}"
                        
                        headlines_data.append({
                            'Rank': i,
                            'Title': headline['title'],
                            'Source': headline['source'],
                            'Time': formatted_time,
                            'Sentiment': headline['sentiment'].title(),
                            'Score': round(headline['sentiment_score'], 3),
                            'Tickers': ', '.join(headline.get('tickers', [])),
                            'Summary': headline.get('summary', '')[:200] + "..." if len(headline.get('summary', '')) > 200 else headline.get('summary', ''),
                        })
                    
                    headlines_df = pd.DataFrame(headlines_data)
                    headlines_df.to_excel(writer, sheet_name='Major_Headlines', index=False)
            
            print(f"✅ Content saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error updating Excel file: {e}")
            return ""


def main():
    print("=== Enhanced Alpha Vantage News Generator with Style Selection ===")
    print("📋 Checking dependencies...")
    
    # Check optional dependencies
    try:
        import yfinance
        print("✅ yfinance available")
    except ImportError:
        print("⚠️ yfinance not installed - market data will be limited")
        print("   Install with: pip install yfinance")
    
    try:
        # Enable debug mode to see news filtering
        generator = ProfessionalNewsGenerator(debug_mode=True)
        print("✅ APIs initialized")
        
        # Display available styles
        print("\n" + "="*70)
        print("🎨 AVAILABLE CONTENT STYLES:")
        print("="*70)
        
        styles = generator.get_available_styles()
        for i, (key, info) in enumerate(styles.items(), 1):
            print(f"{i}. {info['name']} ({info['target_seconds']}s)")
            print(f"   {info['description']}")
        
        print("\n" + "="*70)
        print("📋 MAIN OPTIONS:")
        print("1. Generate content with style selection")
        print("2. View major headlines only")
        print("3. Generate content + headlines with style selection")
        print("="*70)
        
        choice = input("Select main option (1-3): ").strip()
        
        if choice == "2":
            # Just show headlines
            generator.display_headlines()
            return
        
        elif choice in ["1", "3"]:
            # Style selection
            print(f"\n🎨 Select Content Style:")
            style_keys = list(styles.keys())
            for i, (key, info) in enumerate(styles.items(), 1):
                print(f"{i}. {info['name']}")
            
            try:
                style_choice = int(input(f"Choose style (1-{len(style_keys)}): ").strip()) - 1
                if 0 <= style_choice < len(style_keys):
                    selected_style = style_keys[style_choice]
                    selected_name = styles[selected_style]['name']
                    print(f"✅ Selected: {selected_name}")
                else:
                    print("⚠️ Invalid selection, using Classic Daily Brief")
                    selected_style = "classic_daily"
            except (ValueError, IndexError):
                print("⚠️ Invalid input, using Classic Daily Brief")
                selected_style = "classic_daily"
            
            # Generate content with selected style
            content = generator.generate_content(style_key=selected_style)
            
            # Display results
            print("\n" + "="*60)
            print(f"📺 GENERATED SCRIPT ({content['style']}):")
            print("="*60)
            print(content['script'])
            
            print("\n" + "="*60)
            print("📱 SOCIAL MEDIA POST:")
            print("="*60)
            print(content['social_post'])
            
            print("\n" + "="*60)
            print("🎬 MOTION SCRIPT:")
            print("="*60)
            print(content['motion_script'])
            
            print("\n" + "="*60)
            print("📺 VIDEO CAPTION:")
            print("="*60)
            print(content['video_caption'])
            
            print("\n" + "="*60)
            print("🎯 EPISODE TITLE:")
            print("="*60)
            print(content['episode_title'])
            
            if choice == "3":
                # Also show headlines
                print("\n")
                generator.display_headlines()
            
            # Save to Excel
            filename = generator.save_to_excel(content)
            if filename:
                print(f"\n✅ Content saved to: {filename}")
                print(f"📊 Style used: {content['style']}")
                print("📊 Excel file includes Major_Headlines tab with improved filtering")
            
            # Show generation summary
            print("\n" + "="*60)
            print("📊 GENERATION SUMMARY:")
            print("="*60)
            print(f"Style: {content['style']}")
            print(f"Day: {content['day']}")
            print(f"Type: {content['type']}")
            print(f"News articles processed: {content['news_count']}")
            print(f"Script length: {len(content['script'])} characters")
            print(f"Word count: {len(content['script'].split())} words")
            print(f"Motion script length: {len(content['motion_script'])} characters")
            print(f"API calls made: {generator.call_count}")
        
        else:
            print("⚠️ Invalid option selected")
            return
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify .env file contains ALPHA_VANTAGE_API_KEY and OPENAI_API_KEY")
        print("2. Check API key validity and quotas")
        print("3. Ensure internet connection is stable")
        print("4. Install required packages: pip install openai python-dotenv pandas openpyxl")


if __name__ == "__main__":
    main()
