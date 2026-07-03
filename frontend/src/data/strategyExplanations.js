export const STRATEGY_EXPLANATIONS = {
    // ═════════════════════════════════════════
    // Core Baseline
    // ═════════════════════════════════════════
    "BUY_HOLD": {
        "English": {
            title: "Buy & Hold",
            concept: "This strategy involves investing money on Day 1 and holding the position continuously. It acts as a baseline benchmark to compare the performance of active trading models over the long term.",
            theMath: "Return = (Current Price / Buy Price) - 1",
            example: "Buying shares of a stock on January 1st and holding them through all market movements until the end of the year.",
            entry: "Entry is taken on the first day of the simulation.",
            exit: "The position is held until the backtest ends; there is no exit condition."
        },
        "Hinglish": {
            title: "Buy & Hold",
            concept: "Is strategy mein Day 1 par invest karke position ko lagatar hold kiya jaata hai. Yeh ek benchmark kitarah use hota hai jisse dusri active trading strategies ke performance ko compare kiya ja sake.",
            theMath: "Return = (Current Price / Buy Price) - 1",
            example: "Jan 1st ko shares kharid kar, market ke utar-chadav ke bawajood saal ke aakhir tak unhe hold karna Buy & Hold kahlata hai.",
            entry: "Simulation ke pehle din hi Entry li jaati hai.",
            exit: "Isme koi Exit nahi hota. Jab tak simulation end nahi hota tab tak hold kiya jaata hai."
        },
        "Telgish": {
            title: "Buy & Hold",
            concept: "Modati roju invest chesi aa position ni continuous ga alage unche strategy idi. Vere active trading strategies performance ni compare cheyadaniki idi oka benchmark laaga varisthundi.",
            theMath: "Return = (Current Price / Buy Price) - 1",
            example: "January 1st roju shares koni, market ups and downs vachina kuda year end daka alage unchadam.",
            entry: "Simulation start aina modati roje Entry teesukuntamu.",
            exit: "Deentlo Exit undadu. Test end aye daka hold chestune untamu."
        }
    },

    // ═════════════════════════════════════════
    // Trend Following
    // ═════════════════════════════════════════
    "SMA_CROSSOVER": {
        "English": {
            title: "Simple Moving Average (SMA) Crossover",
            concept: "This strategy uses two averages: a short-term indicator (Fast SMA) and a long-term indicator (Slow SMA). An entry occurs when the short-term average crosses above the long-term average, indicating upward price movement.",
            theMath: "SMA = (Sum of closing prices over X days) / X",
            example: "If a stock closed at 100, 102, 104 over 3 days, the 3-day SMA is 102. When the 50-day SMA crosses above the 200-day SMA, an Entry signal is generated.",
            entry: "Fast SMA crosses strictly above the Slow SMA.",
            exit: "Fast SMA crosses strictly below the Slow SMA."
        },
        "Hinglish": {
            title: "Simple Moving Average (SMA) Crossover",
            concept: "Is strategy mein do averages use hote hain: ek short-term (Fast SMA) aur ek long-term (Slow SMA). Jab short-term average, long-term average ki line cross karke upar aata hai, tab Entry generate hoti hai.",
            theMath: "SMA = (Pichle X dinon ke closing prices ka Total) / X",
            example: "Agar stock 3 din 100, 102, 104 par close hua, toh 3-day SMA 102 hota hai. Jab 50-day line 200-day line ko upar ki taraf cross karti hai, tab Entry milti hai.",
            entry: "Jab Fast SMA line Slow SMA line ke upar nikal jaaye.",
            exit: "Jab Fast SMA line Slow SMA line ke neeche chali jaaye."
        },
        "Telgish": {
            title: "Simple Moving Average (SMA) Crossover",
            concept: "Ee strategy rendu aversges ni use chestundi: oka short-term (Fast SMA) mariyu oka long-term (Slow SMA). Short-term average, long-term average ni daati paiki vachinappudu Entry signal vastundi.",
            theMath: "SMA = (Gata X rojulalo closing prices mottham) / X",
            example: "Oka stock 3 rojulu 100, 102, 104 daggara close aithe, 3-day SMA 102 avtundi. 50-day SMA, 200-day SMA ni paiki cross chesinappudu Entry signal ostundi.",
            entry: "Fast SMA, Slow SMA kante paiki cross ainappudu.",
            exit: "Fast SMA, Slow SMA kante kinda ki cross ainappudu."
        }
    },
    "EMA_CROSSOVER": {
        "English": {
            title: "Exponential Moving Average (EMA) Crossover",
            concept: "Similar to the SMA Crossover, but EMA applies more weight to recent prices. It calculates the moving average in a way that reacts to new price data faster than a simple moving average.",
            theMath: "EMA = (Close - Previous EMA) × Multiplier + Previous EMA",
            example: "When prices drop suddenly, the fast EMA line declines earlier than the SMA line, triggering an Exit signal based on the more recent price data.",
            entry: "Fast EMA crosses strictly above the Slow EMA.",
            exit: "Fast EMA crosses strictly below the Slow EMA."
        },
        "Hinglish": {
            title: "Exponential Moving Average (EMA) Crossover",
            concept: "Yeh SMA Crossover jaisa hi hai, lekin EMA recent prices par zyada dhyan deta hai. Yeh calculation price mein aaye naye changes par SMA se jaldi react karti hai.",
            theMath: "EMA = (Close - Pichla EMA) × Multiplier + Pichla EMA",
            example: "Agar price achanak girta hai, toh fast EMA line SMA ke mukable pehle neeche aati hai, aur Exit signal generate karti hai.",
            entry: "Jab Fast EMA line Slow EMA line ke upar nikal jaaye.",
            exit: "Jab Fast EMA line Slow EMA line ke neeche chali jaaye."
        },
        "Telgish": {
            title: "Exponential Moving Average (EMA) Crossover",
            concept: "Idi SMA crossover laanti de, kaani EMA recent prices ki ekkuva weightage istundi. Simple moving average kante ee calculation kottha price data ki fast ga react avtundi.",
            theMath: "EMA = (Close - Patha EMA) × Multiplier + Patha EMA",
            example: "Price sudden ga padinappudu, fast EMA line SMA line kante munduga kinda ki padi Exit signal istundi.",
            entry: "Fast EMA, Slow EMA kante paiki cross ainappudu.",
            exit: "Fast EMA, Slow EMA kante kinda ki cross ainappudu."
        }
    },
    "PRICE_ABOVE_SMA": {
        "English": {
            title: "Price Above SMA",
            concept: "This strategy uses a single moving average. It compares the current closing price to this moving average. If the price is above the line, it indicates an upward trajectory, triggering an Entry.",
            theMath: "Compares current Close price directly against the calculated Moving Average.",
            example: "If the 200-day average price of a stock is 3500, and today it closes at 3550, the price is above the average, generating an Entry signal.",
            entry: "Price crosses strictly above the specified Moving Average line.",
            exit: "Price crosses strictly below the specified Moving Average line."
        },
        "Hinglish": {
            title: "Price Above SMA",
            concept: "Is strategy mein ek hi moving average use hota hai. Yeh aaj ke price aur us average ko compare karta hai. Jab tak price is average line ke upar rahta hai, Entry signal bana rahta hai.",
            theMath: "Current Close price aur us din ki Moving Average value ka comparison.",
            example: "Agar kisi stock ka 200-day average 3500 hai, aur aaj price 3550 par close ho, toh price average se upar hone ke karan Entry milti hai.",
            entry: "Jab price average line ke upar close ho.",
            exit: "Jab price average line ke neeche close ho."
        },
        "Telgish": {
            title: "Price Above SMA",
            concept: "Deentlo okate moving average line geestaaru. Eroju price ni aa average line tho compare chestaru. Price aa line paina unnantha sepu Entry signal active ga untundi.",
            theMath: "Current closing price ni Moving Average value tho compare chestundi.",
            example: "Oka stock 200-day average price 3500 unte, eroju 3550 daggara close aythey, price average kante paina undi kabatti Entry signal vastundi.",
            entry: "Price average line kante paiki cross ayi close ainappudu.",
            exit: "Price average line kante kinda ki cross ayi close ainappudu."
        }
    },
    "TRIPLE_MA": {
        "English": {
            title: "Triple Moving Average",
            concept: "This strategy checks three different moving averages (short, medium, and long-term). It requires the short-term average to be above the medium-term average, which in turn must be above the long-term average.",
            theMath: "Condition: Fast SMA > Medium SMA > Slow SMA",
            example: "An Entry is signaled when the 20-day SMA is higher than the 50-day SMA, and the 50-day SMA is simultaneously higher than the 200-day SMA.",
            entry: "Fast SMA is strictly above Medium SMA, AND Medium is above Slow SMA.",
            exit: "The order is broken (e.g. Fast SMA drops below Medium SMA)."
        },
        "Hinglish": {
            title: "Triple Moving Average",
            concept: "Ismein teen aalag-aalag moving averages (short, medium, long) ka order check kiya jaata hai. Short-term ko medium ke upar, aur medium ko long-term ke upar hona zaroori hai.",
            theMath: "Condition: Fast SMA > Medium SMA > Slow SMA",
            example: "Jab 20-day line 50-day line se upar ho, aur wahi 50-day line 200-day line se upar ho, tabhi Entry signal generate hota hai.",
            entry: "Jab Fast SMA, Medium ke upar ho, AUR Medium SMA, Slow ke upar ho.",
            exit: "Jab yeh order toot-ta hai (jaise Fast SMA, Medium ke neeche aa jaye)."
        },
        "Telgish": {
            title: "Triple Moving Average",
            concept: "Idi moodu veru veru moving averages (short, medium, long) lani check chestundi. Short-term average medium paina undali, laage medium average long paina undali.",
            theMath: "Condition: Fast SMA > Medium SMA > Slow SMA",
            example: "20-day SMA line 50-day SMA paina undi, adhe samayam lo 50-day line 200-day paina unte, Entry signal ostundi.",
            entry: "Fast SMA Medium SMA paina, mariyu Medium SMA Slow SMA paina unnappudu maatrame.",
            exit: "Aa order break ayinappudu (ex: Fast SMA, Medium kinda padipothe)."
        }
    },
    "SUPERTREND": {
        "English": {
            title: "SuperTrend",
            concept: "SuperTrend functions as a dynamic level that trails behind the current price. It calculates a band using an asset's volatility (Average True Range) to identify the direction of the trend.",
            theMath: "Band = (High + Low)/2 ± (Multiplier × ATR)",
            example: "If the asset's price is above the calculated SuperTrend line, the line remains below the price. If the price falls below this band, it signals a trend change and triggers an Exit.",
            entry: "Price crosses above the upper SuperTrend band.",
            exit: "Price falls below the lower SuperTrend band."
        },
        "Hinglish": {
            title: "SuperTrend",
            concept: "SuperTrend ek trailing line ki tarah kaam karta hai. Yeh volatility (ATR) ki calculation use karke trend ka direction aur uski limit tay karta hai.",
            theMath: "Band = (High + Low)/2 ± (Multiplier × ATR)",
            example: "Jab tak price SuperTrend line ke upar rahta hai, line neeche chalti hai. Agar price us line ko tod kar neeche aa jaye, iska matlab trend badal gaya hai aur Exit milta hai.",
            entry: "Jab price apne SuperTrend band ke upar nikal vaha cross kare.",
            exit: "Jab price apne SuperTrend band ke neeche gir jaaye."
        },
        "Telgish": {
            title: "SuperTrend",
            concept: "SuperTrend oka dynamic line la price venakane untundi. Idi volatility (ATR) ni use cheskuni, price trend ey direction lo undho identify cheyadaniki oka band draw chestundi.",
            theMath: "Band = (High + Low)/2 ± (Multiplier × ATR)",
            example: "Price paiki veltunappudu, SuperTrend daani kinda untundi. Okavela price aa line kanadiki vachindante, daani ardham trend marindi, appudu Exit signal ostundi.",
            entry: "Price tana SuperTrend band paiki cross ainappudu.",
            exit: "Price tana SuperTrend band kinda ki padipoyinappudu."
        }
    },

    // ═════════════════════════════════════════
    // Mean Reversion
    // ═════════════════════════════════════════
    "RSI_MEAN_REVERSION": {
        "English": {
            title: "RSI Mean Reversion",
            concept: "The Relative Strength Index (RSI) measures the magnitude of recent price changes. When the RSI falls below a certain threshold (e.g., 30), it is characterized as oversold. The strategy targets a return to the average price.",
            theMath: "RSI = 100 - [100 / (1 + (Average Gain / Average Loss))]",
            example: "If a stock's price declines resulting in an RSI of 25, an Entry signal is triggered based on the expectation that the price will revert to its mean.",
            entry: "RSI drops below the set Oversold threshold (e.g., 30).",
            exit: "RSI rises above the set Overbought threshold (e.g., 70)."
        },
        "Hinglish": {
            title: "RSI Mean Reversion",
            concept: "Relative Strength Index (RSI) recent price movement ka calculation hai. Jab RSI apni ek fixed level (jaise 30) ke neeche jata hai, use oversold kahte hain, aur yeh price ke waapas aane ka wait karta hai.",
            theMath: "RSI = 100 - [100 / (1 + (Average Gain / Average Loss))]",
            example: "Agar lagataar girne se kisi stock ka RSI 25 tak aa jaye, toh Entry milti hai taaki price ke wapas normal aane par use close kiya jaaye.",
            entry: "Jab RSI ek level (jaise 30) ke neeche chala jaaye.",
            exit: "Jab RSI upper level (jaise 70) ke upar chala jaaye."
        },
        "Telgish": {
            title: "RSI Mean Reversion",
            concept: "Relative Strength Index (RSI) recent price changes ni kolustundi. RSI oka limit (like 30) kante taggithe, daanni oversold antaru. Price tana average daggarki malli vasthundi ani e strategy base avtundi.",
            theMath: "RSI = 100 - [100 / (1 + (Average Gain / Average Loss))]",
            example: "Price gattiga padipovadam valla RSI 25 ki vasthe, oversold conditions catch chesi Entry teesukuntundi.",
            entry: "RSI oversold margin (ex: 30) kante kindiki padinappudu.",
            exit: "RSI overbought margin (ex: 70) kante paiki vellinappudu."
        }
    },
    "RSI_2_MR": {
        "English": {
            title: "RSI(2) Mean Reversion",
            concept: "This strategy uses the same RSI calculation but over a very short time window of 2 days. It tracks immediate, short-term price drops rather than broader trends.",
            theMath: "RSI calculation restricted to a 2-period lookback window.",
            example: "If the price drops consecutively over two days causing the RSI(2) to drop below 10, an Entry is placed. An Exit follows when the RSI moves back to the middle range.",
            entry: "RSI(2) drops below the lower threshold (e.g., 5 or 10).",
            exit: "RSI(2) rises above the midway threshold (e.g., 50 or 70)."
        },
        "Hinglish": {
            title: "RSI(2) Mean Reversion",
            concept: "Yeh strategy RSI hi use karti hai lekin sirf pichle 2 din ke data par. Iska primary kaam recent dino ke sudden price drops ko track karna hai.",
            theMath: "Sirf 2-din ka lookback window use karke RSI calculate karna.",
            example: "Agar pichle do dino mein price girne se RSI(2) 10 ke neeche chala jaye, toh Entry li jaati hai. Jaise hi RSI waapas beech me aaye, Exit nikalta hai.",
            entry: "Jab RSI(2) apne oversold level (jaise 10) ke neeche ho.",
            exit: "Jab RSI(2) wapas 50 ya 70 ke aas paas aa jaye."
        },
        "Telgish": {
            title: "RSI(2) Mean Reversion",
            concept: "Deentlo ade RSI calculation vadataru kani kevalam 2 rojula time window ki matrame. Idi pedda trends kante mukhaynga ventane jarige short-term price drops ni track chestundi.",
            theMath: "RSI 2-period window meeda calculation cheyadam.",
            example: "Rendu rojulu varasaga price padadam valla RSI(2) 10 kante kina padithe Entry ostundi. RSI malli madhyaloki rabagane Exit vastundi.",
            entry: "RSI(2) kinda specified level (like 10) padipoyinappudu.",
            exit: "RSI(2) thirigi 50 or 70 cross ainappudu."
        }
    },
    "WILLIAMS_R": {
        "English": {
            title: "Williams %R Mean Reversion",
            concept: "Williams Percent Range (%R) is a momentum indicator that calculates where the current price sits within its highest and lowest ranges. Its scale runs in negative values from -100 to 0.",
            theMath: "%R = (Highest High - Close) / (Highest High - Lowest Low) × -100",
            example: "If the indicator records a value of -90, the price is located near the bottom of its historical range, registering an Entry condition.",
            entry: "Williams %R falls below its oversold threshold (e.g., -80).",
            exit: "Williams %R moves above the exit threshold (e.g., -20)."
        },
        "Hinglish": {
            title: "Williams %R Mean Reversion",
            concept: "Williams %R ek momentum indicator hai jo check karta hai current price apne pichle upper aur lower range me kahan par hai. Iska scale -100 se 0 tak negative mein chalta hai.",
            theMath: "%R = (Highest High - Close) / (Highest High - Lowest Low) × -100",
            example: "Agar value -90 tak pahunch jaaye, iska matlab hai price apne ab tak ki puri range ke sabse lower end pe hai, isliye waha Entry milti hai.",
            entry: "Jab %R apne lower level (e.g., -80) ke neeche dikhai de.",
            exit: "Jab %R wapas upper level (e.g., -20) ke upar aa jaye."
        },
        "Telgish": {
            title: "Williams %R Mean Reversion",
            concept: "Williams %R anedi tana past highest and lowest levels madyalo current price ekkada undo evaluate chestundi. Dini scale -100 nunchi 0 varuku untundi.",
            theMath: "%R = (Highest High - Close) / (Highest High - Lowest Low) × -100",
            example: "Indicator count -90 vachindi ante, price daani complete history range lowest limits lo undani ardham, ide Entry condition.",
            entry: "%R tana lower threshold line (-80) kante kina chere varaku.",
            exit: "%R tana upper threshold line (-20) daatinappudu."
        }
    },
    "BOLLINGER_MEAN_REVERSION": {
        "English": {
            title: "Bollinger Bands Mean Reversion",
            concept: "Bollinger Bands plot a middle average line with identical upper and lower limit bands. When the price hits the lower limit band, it is considered oversold based on normal volatility distribution.",
            theMath: "Middle = 20-day SMA. Lower Band = Middle - (2 × Standard Deviation)",
            example: "When the stock price drops below the calculated lower band, it triggers an Entry. The exit is triggered when the price returns upward to the middle average.",
            entry: "Price closes below the calculated Lower Bollinger Band.",
            exit: "Price moves back above the Middle SMA line."
        },
        "Hinglish": {
            title: "Bollinger Bands Mean Reversion",
            concept: "Bollinger bands ke beech mein ek average line aur uske upar-neeche limits (bands) hoti hain. Jab price apne lower band tak chala jata hai, toh usko oversold level mana jata hai.",
            theMath: "Middle = 20-day SMA. Lower Band = Middle - (2 × Standard Deviation)",
            example: "Jab stock ka price us lower band ke bahar girti hai, Entry generate hoti hai. Aur jab price waapas beech ki average line par aata hai toh Exit milti hai.",
            entry: "Jab price Lower Bollinger Band ke neeche close de.",
            exit: "Jab price wapas Middle SMA line ke upar aa jaaye."
        },
        "Telgish": {
            title: "Bollinger Bands Mean Reversion",
            concept: "Bollinger Bands oka midlle average line geesi, paiki kindha exact ga render limit bands peduthundi. Price ah kinda band ni touch ainappudu daani oversold gaa recognize chesthundi.",
            theMath: "Middle = 20-day SMA. Lower Band = Middle - (2 × Standard Deviation)",
            example: "Oka stock tana lower band kante kinda end aithe Entry vasthundi. Price malli middle average line daggraki ragane Exit chestham.",
            entry: "Price Lower Bollinger Band kante kinda close ainappudu.",
            exit: "Price malli Middle SMA line paiki vellinappudu."
        }
    },
    "STOCHASTIC_MEAN_REVERSION": {
        "English": {
            title: "Stochastic Mean Reversion",
            concept: "The Stochastic Oscillator assesses where the price closed relative to its price range over a certain number of days to identify overbought or oversold conditions.",
            theMath: "%K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100",
            example: "If a stock traded between 90 and 100 over a period, and today closed at 91, the stochastic reading is evaluated as low, which triggers an Entry.",
            entry: "Stochastic value drops below the lower threshold (e.g., 20).",
            exit: "Stochastic value rises above the upper threshold (e.g., 80)."
        },
        "Hinglish": {
            title: "Stochastic Mean Reversion",
            concept: "Stochastic Oscillator yha dekhta hai ki pichle kuch dinon ki price range ke mukable aaj ka closing price kahan stand karta hai, jisse oversold/overbought ka pata chalta hai.",
            theMath: "%K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100",
            example: "Agar pichle kuch din price 90 se 100 tha, aur aaj price 91 par close hua, to stochastic value bahut kam aayega aur Entry generate hogi.",
            entry: "Jab Stochastic value line apni lower limit (jaise 20) ke neeche jaaye.",
            exit: "Jab Stochastic value apni upper limit (jaise 80) ko touch kare."
        },
        "Telgish": {
            title: "Stochastic Mean Reversion",
            concept: "Stochastic Oscillator anedi gata konni rojula ranges madhyalo erojuti closing price e prantham lo close ayindo count chestundi.",
            theMath: "%K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100",
            example: "Gata rojulalo price 90 nunche 100 boundary la unte, ivla 91 ki vasthe daanini oversold point kinda consider chesi Entry generates avtudi.",
            entry: "Stochastic value specified oversold line (ex: 20) kante kinda paddapudu.",
            exit: "Stochastic value upper limit (ex: 80) cross ayinappudu."
        }
    },
    "ZSCORE_MEAN_REVERSION": {
        "English": {
            title: "Z-Score Mean Reversion",
            concept: "Z-Score is a statistical measurement that calculates how many standard deviations the current price is deviating from its historical average.",
            theMath: "Z-Score = (Current Price - Moving Average) / Standard Deviation",
            example: "If the Z-score moves beyond -2.0, it denotes a highly unusual downward price variance from the mean, triggering an Entry on the probability that it reverts to zero.",
            entry: "Z-Score drops below a defined negative deviation limit (e.g., -2.0).",
            exit: "Z-Score reverts toward the mean line (zero)."
        },
        "Hinglish": {
            title: "Z-Score Mean Reversion",
            concept: "Z-Score ek statistical unit hai. Yeh calculation batata hai ki aaj ka price apne normal average point se kitne standard deviation distance par hai.",
            theMath: "Z-Score = (Current Price - Moving Average) / Standard Deviation",
            example: "Agar calculation value -2.0 ke bhi neeche chali jaaye, toh ye batati hai ki price normal level se bahut gir gaya hai, jisse Entry mil sakti hai.",
            entry: "Jab Z-Score -2.0 jese margin ke neeche aakar close de.",
            exit: "Jab Z-Score wapas normalize (average point 0.0) hone lage."
        },
        "Telgish": {
            title: "Z-Score Mean Reversion",
            concept: "Z-Score anedi statistic parameter. Current price ah stock historical moving average point nunchi enni standard deviations duram ga vundo measure chestundi.",
            theMath: "Z-Score = (Current Price - Moving Average) / Standard Deviation",
            example: "Z-score anedi -2.0 negative value varaku pothe price tana normal avg kante abnormal ga paddatu, daani base cheskuni deento Entry create chestamu.",
            entry: "Z-Score negative variance limit (ex: -2.0) ni daati kinda paddapudu.",
            exit: "Z-Score mean position (zero) daggarki revert ayinappudu."
        }
    },

    // ═════════════════════════════════════════
    // Momentum / Breakouts
    // ═════════════════════════════════════════
    "DONCHIAN_BREAKOUT": {
        "English": {
            title: "Donchian Breakout",
            concept: "Donchian Channels identify the highest highs and lowest lows over a specific timeframe. The strategy detects an upward momentum shift when the price breaks above the previous highest high.",
            theMath: "Upper Band = Highest High value recorded over the previous X days",
            example: "If the highest price recorded over 20 days was 120, an Entry is placed the moment the current price rises and closes above 120.",
            entry: "Price crosses and closes above the Donchian Upper Band.",
            exit: "Price drops and closes below the Donchian Lower Band."
        },
        "Hinglish": {
            title: "Donchian Breakout",
            concept: "Donchian Channels pichle X dinon ke sabse highest aur lowest levels ko track karta hai. Jab price pichle highest level ke upar nikalta hai toh strategy naya Entry signal deti hai.",
            theMath: "Upper Band = Pichle X dino mein banaya gaya highest price parameter.",
            example: "Agar 20 din me kisi stock ka highest price 120 raha hai, toh jaise hi price 120 ko daat kar close karegi, wo apne Upper Band ko todti hai aur waha Entry banta hai.",
            entry: "Jab price Donchian ke Upper Band line ko cross karke close kare.",
            exit: "Jab price Donchian Line ke Lower Band ko tod kar neeche close de."
        },
        "Telgish": {
            title: "Donchian Breakout",
            concept: "Donchian channels pichina time period loni highest and lowest peaks ni boundaries gaa vadutundi. Eey highest peak ni daati price paiki velte trend marinattu.",
            theMath: "Upper Band = Gata X rojulalo Highest price entho evaluate chesthundi.",
            example: "20 rola nunchi maximum price point 120 touch ai unte, e rojaiyite ah price 120 point dhatutundo ventane idi oka Entry ni record chestundi.",
            entry: "Price, existing highest high (Upper Band) line painake velli close ainappudu.",
            exit: "Malli lowest low limit (Lower Band) kinda close cheyatam."
        }
    },
    "HIGH_BREAKOUT": {
        "English": {
            title: "52-Week High Breakout",
            concept: "This strategy monitors if an asset surpasses its highest achieved price point over the preceding 52 weeks (approx 252 trading days), an indicator of strong underlying momentum.",
            theMath: "Current Price > Max(High) over the last 252 days",
            example: "If the current closing price crosses the absolute high value set anytime in the last year, it triggers an Entry.",
            entry: "Price closes above the highest point recorded in the last 252 trading days.",
            exit: "Price falls back below a given trailing parameter or moving average."
        },
        "Hinglish": {
            title: "52-Week High Breakout",
            concept: "Yeh strategy dhyan deti hai ki kya kisi stock ne apne pichle ek saal (52 hafte) ka highest price cross kiya hai, jo strong market momentum ko show karta hai.",
            theMath: "Current Price > Pichle 252 dino ka Highest Price record.",
            example: "Agar latest closing price apne pure 1 saal ke maximal price level se aage nikal jaye, toh usi point par Entry milti hai.",
            entry: "Jaise hi closing price apne last 1-year mark ke high se aage close hota hai.",
            exit: "Jab price momentum kho kar kisi average ke neeche gir jaye."
        },
        "Telgish": {
            title: "52-Week High Breakout",
            concept: "Edaina asset tana pichila 52-weeks loni highest top point ni daati move aytunda Leda ani e strategy track chestundi, adi okavela daatite strong momentum unattu ardham.",
            theMath: "Current Price > Last 252 rojulalo Maximal recorded price avvali.",
            example: "Evaluation period loni closing price tana gata oka samvastaram highest parameter kanna paiki cross chesunte adhi oka Entry avuthundi.",
            entry: "Latest close point, aa year-high mark kante paiki cross ayi close ainappudu.",
            exit: "Ah momentum nilabettukaleka trailing average kinda padinappudu."
        }
    },
    "ROC_MOMENTUM": {
        "English": {
            title: "Rate of Change (ROC) Momentum",
            concept: "The ROC measures the percentage change in price between the current close and the close N days ago. It evaluates the velocity of the price trend.",
            theMath: "ROC = [(Current Close - NDaysAgo Close) / NDaysAgo Close] × 100",
            example: "If the calculated ROC over 20 days crosses above the zero line into positive territory, an Entry is confirmed.",
            entry: "ROC metric crosses above the 0 baseline into positive numbers.",
            exit: "ROC metric drops below 0."
        },
        "Hinglish": {
            title: "Rate of Change (ROC) Momentum",
            concept: "ROC percent me change batata hai. Yeh measure karta hai aaj ka closing price, N din pehle ke closing price se kitna differ kar raha hai.",
            theMath: "ROC = [(Aaj ka Close - Pichla N_Days_ka_Close) / Pichla N_Days_ka_Close] × 100",
            example: "Agar 20 din ka interval measure kiya jaye aur wo (0) line ko daat kar upar chali jaye, toh wahan se valid Entry generate hoti hai.",
            entry: "Jab ROC line 0 ke point se upar cross kare.",
            exit: "Jab ROC line vapas apne zero baseline ke neeche aa jaye."
        },
        "Telgish": {
            title: "Rate of Change (ROC) Momentum",
            concept: "Evalati price ki mariyu, gata N day period price ki madyana percent difference enta vundo yee ROC indicator measure chestundi.",
            theMath: "ROC = [(Eroje close - paatha N_days close) / paatha N_days close] × 100",
            example: "20-days loni ROC count positive zero mark percentage paina velithunte dhanitho Entry record generate authundi.",
            entry: "ROC calculation count zero (0) line daati positive vachinappudu.",
            exit: "ROC calculation line malli kinda padi zero cross ayinappudu."
        }
    },
    "MOMENTUM_12_1": {
        "English": {
            title: "12-1 Momentum",
            concept: "A strategy that calculates momentum over an 11-month period. It takes the performance over the last 12 months but subtracts the most recent 1 month to exclude immediate short-term volatility.",
            theMath: "Rate of return calculated from (Today minus 12 months) to (Today minus 1 month).",
            example: "If the calculated return omitting the final 30 days is positive, an Entry is placed. If negative, no entry is taken.",
            entry: "The 12-to-1 month historical return evaluates to a positive number.",
            exit: "The 12-to-1 month historical return falls below zero."
        },
        "Hinglish": {
            title: "12-1 Momentum",
            concept: "Ye strategy pichle 12 months ka performance check karti hai, but usme se carefully latest ek mahine ko exclude kar deti hai takki immediate variation avoid kar sake.",
            theMath: "(Present - 12 mahine) se leke (Present - 1 mahina) tak ka return calculation.",
            example: "Agar aakhri 30 din ko chod kar baki 11 months measurement ka net return positive nikle toh Entry place hoti hai.",
            entry: "Jab ye specifically evaluate kiya gya return rate positive zone mein ho.",
            exit: "Jab yeh measurement percentage zero se negative mein aa jaye."
        },
        "Telgish": {
            title: "12-1 Momentum",
            concept: "Gata 12 nelala mottham time lo, last exactly 1 month performance result teesesesi appudu momentum ni kolustaru yee strategy lo, indhu valla fluctuations vastayani.",
            theMath: "(Present date - 1 year) nunchi (Present date - 1 month) lopala calculation.",
            example: "Last 30 days mathram vidchi, migatavanni evaluate cheste count gain lo vunte appude strategy Entry create cheyagaladhu.",
            entry: "Ee specific math calculations dwara vacchina percentage positive value unappudu.",
            exit: "Ah calculated line result zero kanna nethiki padipoyinappudu."
        }
    },
    "MA_SLOPE_MOMENTUM": {
        "English": {
            title: "MA Slope Momentum",
            concept: "This evaluates the directional change of a moving average itself. If the moving average value is steadily increasing, the slope is positive, indicating upward momentum.",
            theMath: "Slope = (Current Moving Average value) - (Previous Moving Average value)",
            example: "If the 50-day SMA evaluated today is higher than it was yesterday, the slope registers as positive, resulting in an Entry.",
            entry: "The defined Moving Average slope evaluates slightly greater than 0.",
            exit: "The slope becomes flat or trends downward below 0."
        },
        "Hinglish": {
            title: "MA Slope Momentum",
            concept: "Ye kewal Moving Average ke khudke direction par depend karti hai. Agar moving average value har din pehle se badh rahi hai, toh slope positive gina jayega.",
            theMath: "Slope = (Aaj ki Moving Average value) - (Pichle din ki Moving Average value)",
            example: "Agar 50 din ka average result kal se aaj zyaada aaya hai (Positive Slope), to wahaan turant ek naya Entry valid ban jata hai.",
            entry: "Jab MA line ka mathematically calculated slope positive me badhne lage.",
            exit: "Jab MA line sidhi ho jaye ya dhire se neeche aane lage."
        },
        "Telgish": {
            title: "MA Slope Momentum",
            concept: "Moving Average line geetha direct ga elanti malupu tiskuntundi anedanni slope momentum base cheskuni verify chestaru.",
            theMath: "Slope = (Current Moving average point) - (Previous Moving average point)",
            example: "50-days SMA point ninatiki, erojuki observe cheste value penchuthonda (Positive value vastundaa) ani check chesi Entry point thiskuntaru.",
            entry: "MA line mathematically calculate aina slope zero kante positive vachinappudu.",
            exit: "MA line slope neutral leda negative lo jaripoyinappudu."
        }
    },
    "PRICE_HIGH_MOMENTUM": {
        "English": {
            title: "Price vs N-Day High",
            concept: "This strategy verifies whether the asset's current closing price is located within a very close percentage threshold of its recent historical maximum.",
            theMath: "Check if (Current Price) > (Highest High of N Days * specific fractional boundary).",
            example: "If the threshold is set to 95%, the stock must be trading no more than 5% below its recent absolute peak to trigger an Entry.",
            entry: "Price reaches and closes above the fractional boundary near the high limit.",
            exit: "Price falls far from its recent peak."
        },
        "Hinglish": {
            title: "Price vs N-Day High",
            concept: "Ismein sirf yahi parakha jata hai ki aaz ka closing price pichle N din ki highest price record ke kitna karib trade ho raha hai.",
            theMath: "Calculation is if (Aaj ka price) > (Highest value * Fractional parameter).",
            example: "Agar condition 95% par set ki hai, toh stock apni maximum level ke bas 5% drop tak ki range mein ho toh entry trigger consider ki jayegi.",
            entry: "Jab closing price is specified higher parameter ki limit tak touch kare.",
            exit: "Jab point limit wapas average distance par chali aye or girne lag pade."
        },
        "Telgish": {
            title: "Price vs N-Day High",
            concept: "Asset erojuti closing count vachi gata varam maximum peaks enthavaraku cherdhindo observe chesi chustundi. Percentage close boundary paine Entry dorkuthai.",
            theMath: "Logic idhi (Current Price) > (Highest limit * fractional border ratio).",
            example: "Boundary parameter 95% ga set chesthe, ah 5% deviation lopalne price unteyane idi stock point entry register autundi.",
            entry: "Price margin cross ai absolute higher highest mark daggarlo close appude.",
            exit: "Price parameters low positions nunchi kinchen paddapudu."
        }
    },
    "ABSOLUTE_MOMENTUM": {
        "English": {
            title: "Absolute Momentum",
            concept: "Absolute momentum compares the asset's current price solely to its own past price over a set period. It requires the return to be mathematically greater than zero.",
            theMath: "Return calculated from (Today) compared against (N Days Ago) > 0.",
            example: "If the closing price is higher today than it was strictly 12 months ago, the absolute return is positive, and an Entry is processed.",
            entry: "The N-day percentage return limit is strictly greater than zero.",
            exit: "The N-day percentage return becomes zero or negative."
        },
        "Hinglish": {
            title: "Absolute Momentum",
            concept: "Ye measure karta hai ki aaj ka closing asset price, exact pichle samay window limit se compare karne k baad usse uupar hai ya neeche. Positive me ho to return valid h.",
            theMath: "Calculation parameter: (Aaj ka Price) vs (N din pehle ka price) > Zero.",
            example: "Agar result ekal fixed duration (1 year back) par, pehle se return score better dikhay to Entry create hota h.",
            entry: "Jab interval check ka percentage return exactly positive generate kare limit.",
            exit: "Jab time duration parameters ka net return zero (0) ya aur negative ho."
        },
        "Telgish": {
            title: "Absolute Momentum",
            concept: "Current price nunchi specific ga thelna period limit madhya price gap mathrame enthavaraku undo maths params check chestaayi.",
            theMath: "Condition: (Recent price) with compared against (N days back price) > Zero.",
            example: "1 year past data varaku stock eroju compare set chesinapudu percentage strictly greater unappude deenti vallana Entry count avtundi.",
            entry: "Specific period timeline calculation limit positive result isthe gani.",
            exit: "Total percent parameter zero or danikaante negtative ayinappudu."
        }
    }
};

export const DEFAULT_EXPLANATION = {
    "English": {
        title: "Strategy Overview",
        concept: "A quantitative trading model that evaluates market movements based on specified mathematical indicators.",
        theMath: "Algorithmic computation executed upon historical OHLCV data structures.",
        example: "The model scans available historical data and evaluates conditions based on its parameters.",
        entry: "Determined conditionally based on strategy parameters.",
        exit: "Determined conditionally based on strategy parameters."
    },
    "Hinglish": {
        title: "Strategy Overview",
        concept: "Yeh ek mathematical quantitative model hai jo specified market movements aur data indicators read karta hai.",
        theMath: "Pure historical OHLCV parameter metrics pe based algorithmic computation.",
        example: "Historical data evaluate karke strategy apne parameters ke hisaab se condition fulfill hone par position trace karti hai.",
        entry: "Core logic aur specified strategy boundaries ke base par set hota hai.",
        exit: "Core logic aur specified strategy boundaries ke base par set hota hai."
    },
    "Telgish": {
        title: "Strategy Overview",
        concept: "Idoka strategy mathematical quantitative modeling method, market loni price values track dwara pani chestadi.",
        theMath: "Evaluation parameter base data loni history, volume and numbers tho calculation jaruthndi.",
        example: "Patha historical points set chesukoni calculations verify authunnayi condition batti.",
        entry: "Strategy definechesina conditions limit paina parameter base avtai.",
        exit: "Strategy definechesina conditions limit paina parameter base avtai."
    }
};
