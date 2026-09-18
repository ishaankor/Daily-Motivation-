import random
from datetime import date, timedelta, datetime
import os
import socket
import psycopg2
import requests
from requests import auth
from dotenv import load_dotenv
from mysql.connector import Error
from datetime import datetime
import tweepy
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter
import io
import sys


# Handle PyInstaller bundled app
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Load environment variables - handle both development and bundled executable
env_path = get_resource_path('Twitter_Bot_Setup/.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
else:
    # Fallback to current directory
    load_dotenv()
    print("Loaded .env from current directory")

api_key = os.getenv("API_KEY")
api_secret_key = os.getenv("API_SECRET_KEY")
api_bearer_token = os.getenv("API_BEARER_TOKEN")
api_access_token = os.getenv("API_ACCESS_TOKEN")
api_secret_access_token = os.getenv("API_SECRET_ACCESS_TOKEN")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
account_id = os.getenv("ACCOUNT_ID")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE")

authenticator = tweepy.OAuth1UserHandler(api_key, api_secret_key,
                                         api_access_token,
                                         api_secret_access_token)
api = tweepy.API(authenticator)

day_index = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}
reversed_day_mappings = {v: k for k, v in day_index.items()}


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


def check_wifi_connection():
    try:
        google_socket = socket.create_connection(("www.google.com", 80))
        if google_socket is not None:
            google_socket.close()
        return True
    except OSError:
        pass
    return False


def make_wifi_connection():
    name_of_wifi = os.getenv("WIFI_NAME")
    if os.name == 'nt':
        os.system('netsh interface set interface "Wi-Fi" disabled')
        os.system('netsh interface set interface "Wi-Fi" enabled')
        os.system(f'''cmd /c "netsh wlan connect name={name_of_wifi}"''')
    else:
        print("WiFi reconnection only supported on Windows")


def run_internet_check():
    if check_wifi_connection() is False:
        make_wifi_connection()
    else:
        print("Wifi connection is strong.")


def create_server_connection(user_name, user_password, host="localhost", port="5432", sslmode="prefer"):
    connection = None
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            user=user_name,
            password=user_password,
            sslmode=sslmode
        )
        print("Postgres connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return connection


def create_database(connection_prompt, query):
    cursor = connection_prompt.cursor()
    try:
        cursor.executemany(query)
        cursor.commit()
        print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")


def create_db_connection(user_name, user_password, db_name, host="localhost", port="5432", sslmode="prefer"):
    psql_connection = None
    try:
        psql_connection = psycopg2.connect(
            host=host,
            port=port,
            user=user_name,
            password=user_password,
            database=db_name,
            # sslmode=sslmode
            # pool_mode="transaction"
        )
        print("Postgres Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return psql_connection


def execute_query(connection_prompt, query):
    cursor = connection_prompt.cursor()
    try:
        cursor.execute(query)
        connection_prompt.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")


def tweet_image(photo_url, message):
    client = tweepy.Client(api_bearer_token, api_key, api_secret_key,
                           api_access_token, api_secret_access_token)
    tweeper = tweepy.API(authenticator)

    file_format = find_file_format(photo_url)
    filename = f"temp{file_format}"
    request = requests.get(photo_url, stream=True)
    if request.status_code == 200:
        # with open(filename, 'wb') as image:
        #     for chunk in request:
        #         image.write(chunk)

        try:
            media = tweeper.media_upload(filename)
            sunday_tweet = client.create_tweet(text=message, media_ids=[media.media_id])
            client.create_tweet(
                text="To end this week with a positive note, here is a beautiful work of nature! Let's have a great week ahead of us!",
                in_reply_to_tweet_id=sunday_tweet.data['id'])
            print("Successfully posted image tweet and reply!")

        except Exception as e:
            print(f"Error posting tweet: {e}")
        finally:
            os.remove(filename)
    else:
        print("Unable to download image")


def tweet_for_the_day():
    quotes_file_path = get_resource_path("quotes.txt")
    quotes_file = open(quotes_file_path, "r").read().splitlines()
    picked_quote = random.choice(quotes_file)
    with open(quotes_file_path, "r") as quotes_file:
        lines = quotes_file.readlines()
    with open(quotes_file_path, "w") as quotes_file:
        for line in lines:
            if line.strip("\n") != picked_quote:
                quotes_file.write(line)
    pass
    return picked_quote


def find_file_format(photo_url):
    period_count = 0
    period_index_list = []
    for i in range(len(photo_url)):
        if photo_url[i] == '.':
            period_index_list.append(i)
            period_count += 1
    max_index = period_index_list[len(period_index_list) - 1]
    file_format = photo_url[max_index:max_index + 4]
    return file_format


def photo_for_sunday():
    photo_file_path = get_resource_path("photo_urls.txt")
    photo_file = open(photo_file_path, "r").read().splitlines()
    picked_photo = random.choice(photo_file)
    with open(photo_file_path, "r") as photos_file:
        lines = photos_file.readlines()
    with open(photo_file_path, "w") as photos_file:
        for line in lines:
            if line.strip("\n") != picked_photo:
                photos_file.write(line)
    pass
    return picked_photo


def tweet_poll():
    client = tweepy.Client(api_bearer_token, api_key, api_secret_key,
                           api_access_token, api_secret_access_token)
    motivation_for_the_day = tweet_for_the_day()
    tweet_str = motivation_for_the_day + '\n' + "What do you think about the quote - is it influential to you?" + '\n' + "#AspireToInspire"
    len_tweet_str = len(motivation_for_the_day)
    while len_tweet_str > 154:
        motivation_for_the_day = tweet_for_the_day()
        tweet_str = motivation_for_the_day + '\n' + "What do you think about the quote - is it influential to you?" + '\n' + "#AspireToInspire"
        len_tweet_str = len(tweet_str)
    client.create_tweet(text=tweet_str,
                        poll_options=["Yes, absolutely! \U0001F604",
                                      "Unfortunately, no... \U0001F62B"],
                        poll_duration_minutes=1440)


def get_recent_tweet_data():
    print("Fetching recent tweet data...")
    # Use a more recent start time that the API will accept
    # Twitter's free tier has very limited historical search
    recent_datetime = datetime.now() - timedelta(hours=24)  # Start from 12 hours ago
    start_time_rfc3339 = recent_datetime.isoformat() + "Z"
    print("Looking for tweets since:", start_time_rfc3339)

    # Get username from numeric account_id since search API needs username, not numeric ID
    print(f"Getting username for account ID: {account_id}")
    user_info_request = requests.get(
        url=f"https://api.twitter.com/2/users/{account_id}",
        auth=BearerAuth(api_bearer_token))
    user_info_json = user_info_request.json()

    if 'data' not in user_info_json:
        print(f"Error getting user info: {user_info_json}")
        return 0, ""

    username = user_info_json['data']['username']
    print(f"Using username: {username}")

    user_poll_request = requests.get(
        url=f"https://api.x.com/2/tweets/search/recent?query=from:{username}",
        auth=BearerAuth(api_bearer_token),
        params={"start_time": start_time_rfc3339, "max_results": 10})
    user_poll_json = user_poll_request.json()
    print("User tweets response:", user_poll_json)

    # If we get an error about start_time, try without it
    if 'errors' in user_poll_json:
        print("Got API error, trying without start_time parameter...")
        user_poll_request = requests.get(
            url=f"https://api.x.com/2/tweets/search/recent?query=from:{username}",
            auth=BearerAuth(api_bearer_token),
            params={"max_results": 10})
        user_poll_json = user_poll_request.json()
        print("User tweets response (no start_time):", user_poll_json)

    if 'data' not in user_poll_json or len(user_poll_json['data']) == 0:
        print(f"No recent tweets found for @{username}")
        print("Make sure you have posted tweets recently, or check your account credentials.")
        return 0, ""

    recent_poll_tweeted_id = user_poll_json['data'][0]['id']
    print(f"Most recent tweet ID: {recent_poll_tweeted_id}")

    recent_poll_statistics = requests.get(
        url=f"https://api.twitter.com/2/tweets?ids={recent_poll_tweeted_id}&expansions=attachments.poll_ids&poll.fields=duration_minutes,end_datetime,id,options,voting_status",
        auth=BearerAuth(api_bearer_token))
    recent_poll_statistics_json = recent_poll_statistics.json()
    print("Tweet details response:", recent_poll_statistics_json)

    tweet_content = ""
    if 'data' in recent_poll_statistics_json and len(recent_poll_statistics_json['data']) > 0:
        recent_quote = recent_poll_statistics_json['data'][0]['text']
        tweet_content = recent_quote.replace('\'', "''")
    else:
        print("Error: No tweet text found in API response")

    poll_stats = 0
    if 'includes' in recent_poll_statistics_json and 'polls' in recent_poll_statistics_json['includes']:
        try:
            polls = recent_poll_statistics_json['includes']['polls'][0]
            option_0_votes = polls['options'][0]['votes']
            option_2_votes = polls['options'][1]['votes']

            poll_stats = (option_0_votes / (option_0_votes + option_2_votes)) * 100 if (
                                                                                                   option_0_votes + option_2_votes) > 0 else 0

        except (KeyError, IndexError, ZeroDivisionError) as e:
            print(f"Error calculating poll statistics: {e}")
            poll_stats = 0
    else:
        print("Error: No poll data found in tweet")
    return poll_stats, tweet_content


def get_poll_statistics():
    """Legacy function - now uses combined data fetching"""
    stats, _ = get_recent_tweet_data()
    return stats


def get_recent_tweet():
    """Legacy function - now uses combined data fetching"""
    _, content = get_recent_tweet_data()
    return content


def store_poll_statistics(database, prior_data, date_week):
    prior_day_index = today_weekday - 1
    prior_day = day_index[prior_day_index]
    execute_query(database,
                  f"UPDATE poll_distribution SET {prior_day} = {prior_data} WHERE week = '{date_week}'")


def store_tweet_info(database, prior_info, date_week):
    prior_day_index = today_weekday - 1
    prior_day = day_index[prior_day_index]
    execute_query(database,
                  f"UPDATE tweet_distribution SET {prior_day} = '{prior_info}' WHERE week = '{date_week}'")


def find_best_poll_statistics(psql_database):
    current_date = find_current_date(psql_database)
    week_stat_list = []
    cursor = psql_database.cursor()
    cursor.execute(
        f"SELECT * FROM poll_distribution WHERE week = '{current_date}'")
    week_statistics = cursor.fetchone()
    for w_stat in week_statistics[1:]:
        week_stat_list.append(float(w_stat))
    max_stat = week_stat_list[0]
    try:
        for datapoint in week_stat_list[1:]:
            if datapoint is not None:
                if datapoint > max_stat:
                    max_stat = datapoint
    except ValueError:
        print("Value Error")
        pass
    return max_stat


def find_best_stat_index(psql_database, max_stat):
    current_date = find_current_date(psql_database)
    week_stat_list = []
    cursor = psql_database.cursor()
    cursor.execute(
        f"SELECT * FROM poll_distribution WHERE week = '{current_date}'")
    week_statistics = cursor.fetchone()
    for w_stat in week_statistics[1:]:
        week_stat_list.append(float(w_stat))
    max_stat_index = week_stat_list.index(max_stat)
    index_to_day = day_index[max_stat_index]
    return index_to_day


def retrieve_most_influential_quote(psql_database, day_conversion, date_week):
    cursor = psql_database.cursor()
    cursor.execute(
        f"SELECT {day_conversion} FROM tweet_distribution WHERE week = '{date_week}'")
    parsed_quote = cursor.fetchone()
    full_quote_string = parsed_quote[0]
    return full_quote_string


def create_weekly_poll_graph(psql_database, week_date):
    try:
        cursor = psql_database.cursor()
        cursor.execute(
            f"SELECT * FROM poll_distribution WHERE week = '{week_date}'")
        week_statistics = cursor.fetchone()

        if not week_statistics:
            print("No statistics found for this week")
            return None

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        stats = []

        for w_stat in week_statistics[1:]:
            if w_stat is not None:
                stats.append(float(w_stat))
            else:
                stats.append(0.0)

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))

        try:
            import matplotlib.image as mpimg
            bg_image_path = get_resource_path(
                'starry-night-sky-dark-blue-space-black-and-purple-galaxy-with-cosmic-light-of-planets-shiny-astrology-constellations-with-sparkles-winter-fantasy-gradient-backdrop-milky-way-wallpaper-vector.jpg')
            bg_image = mpimg.imread(bg_image_path)
            ax.imshow(bg_image, extent=[-0.5, 5.5, 0, max(stats) * 1.2 if max(stats) > 0 else 120],
                      aspect='auto', alpha=0.8)
        except Exception as e:
            print(f"Could not load space background image: {e}")
            x = np.linspace(0, 1, 200)
            y = np.linspace(0, 1, 200)
            X, Y = np.meshgrid(x, y)
            Z1 = np.exp(-((X - 0.3) ** 2 + (Y - 0.7) ** 2) / 0.1)
            Z2 = np.exp(-((X - 0.8) ** 2 + (Y - 0.2) ** 2) / 0.15)
            Z3 = np.sin(X * 10) * np.cos(Y * 8) * 0.3
            cosmic_data = Z1 + Z2 * 0.8 + Z3 * 0.2 + np.random.random((200, 200)) * 0.1
            ax.imshow(cosmic_data, extent=[0, 6, 0, 120], cmap='plasma', alpha=0.7, aspect='auto')

        ax.set_xlim(-0.5, 5.5)
        ax.set_ylim(0, max(stats) * 1.2 if max(stats) > 0 else 120)
        colors = ['#FF69B4', '#DA70D6', '#BA55D3', '#9370DB', '#8A2BE2', '#4B0082']
        bars = ax.bar(days, [0] * 6, color=colors, alpha=0.85, edgecolor='none', linewidth=0)
        ax.set_title('Weekly Poll Influential Statistics',
                     fontsize=24, fontweight='bold', pad=35, color='white',
                     fontfamily='serif')
        ax.set_xlabel('Days of the Week', fontsize=18, fontweight='bold', color='white',
                      fontfamily='serif', labelpad=25)
        ax.set_ylabel('Influential Rate (%)', fontsize=18, fontweight='bold', color='white',
                      fontfamily='serif')
        ax.tick_params(axis='x', labelsize=14, colors='white', labelcolor='white')
        ax.tick_params(axis='y', labelsize=14, colors='white', labelcolor='white')
        ax.grid(True, alpha=0.3, linestyle='--', color='white')
        ax.set_facecolor('#1A0D2E')
        ax.set_ylim(0, max(stats) * 1.2 if max(stats) > 0 else 10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('white')
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_color('white')
        ax.spines['bottom'].set_linewidth(2)
        subtitle = ax.text(0.5, 0.95, f'Week: {week_date}', transform=ax.transAxes,
                           ha='center', va='top', fontsize=14, color='white',
                           fontfamily='serif', fontstyle='italic', fontweight='bold')
        text_labels = []
        for i, bar in enumerate(bars):
            text = ax.text(bar.get_x() + bar.get_width() / 2., 0,
                           '', ha='center', va='bottom', fontsize=14,
                           fontweight='bold', color='white', fontfamily='serif')
            text_labels.append(text)

        def animate(frame):
            total_animation_frames = 6 * 10
            if frame < total_animation_frames:
                day_index = min(frame // 10, 5)
                progress = (frame % 10) / 10.0
            else:
                day_index = 5
                progress = 1.0

            for i in range(day_index + 1):
                if i < day_index:
                    bars[i].set_height(stats[i])
                elif i == day_index:
                    current_height = stats[i] * progress
                    bars[i].set_height(current_height)

                if bars[i].get_height() > 0:
                    text_labels[i].set_position((bars[i].get_x() + bars[i].get_width() / 2.,
                                                 bars[i].get_height() + max(stats) * 0.01))
                    text_labels[i].set_text(f'{bars[i].get_height():.1f}%')
                    text_labels[i].set_alpha(1.0)

            if day_index > 0:
                current_stats = stats[:day_index + 1]
                if max(current_stats) > 0:
                    best_day_index = current_stats.index(max(current_stats))
                    for j in range(day_index + 1):
                        bars[j].set_color(colors[j])
                        bars[j].set_alpha(0.8)
                    bars[best_day_index].set_color('#FFD700')
                    bars[best_day_index].set_alpha(1.0)

            if day_index < len(days):
                current_day = days[day_index]
                subtitle.set_text(f'Week: {week_date} | Building up to: {current_day}')
            else:
                subtitle.set_text(f'Week: {week_date} | Complete Week Summary')

            return list(bars) + text_labels + [subtitle]

        frames = 6 * 10 + 10
        anim = FuncAnimation(fig, animate, frames=frames, interval=150, blit=False, repeat=False)

        plt.subplots_adjust(top=0.80, bottom=0.15, left=0.15, right=0.95)

        fig.patch.set_facecolor('#0B0620')
        gif_filename = f"weekly_poll_animation_{week_date.replace('/', '_')}.gif"
        writer = PillowWriter(fps=6)
        anim.save(gif_filename, writer=writer, dpi=80)
        plt.close()

        print(f"Generated animated poll statistics: {gif_filename}")
        return gif_filename

    except Exception as e:
        print(f"Error creating animated poll graph: {e}")
        return create_static_poll_graph(psql_database, week_date)


def create_static_poll_graph(psql_database, week_date):
    try:
        cursor = psql_database.cursor()
        cursor.execute(
            f"SELECT * FROM poll_distribution WHERE week = '{week_date}'")
        week_statistics = cursor.fetchone()

        if not week_statistics:
            print("No statistics found for this week")
            return None

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        stats = []

        for w_stat in week_statistics[1:]:
            if w_stat is not None:
                stats.append(float(w_stat))
            else:
                stats.append(0.0)

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))

        colors = ['#2ECC71', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

        bars = ax.bar(days, stats, color=colors, alpha=0.8, edgecolor='white', linewidth=2)

        for bar, stat in zip(bars, stats):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2., height + max(stats) * 0.01,
                        f'{stat:.1f}%', ha='center', va='bottom', fontsize=12,
                        fontweight='bold', color='white')

        ax.set_title('Weekly Poll Influential Statistics',
                     fontsize=20, fontweight='bold', pad=20, color='white')
        ax.set_xlabel('Days of the Week', fontsize=14, fontweight='bold', color='white')
        ax.set_ylabel('Influential Rate (%)', fontsize=14, fontweight='bold', color='white')

        ax.tick_params(axis='x', labelsize=12, colors='white')
        ax.tick_params(axis='y', labelsize=12, colors='white')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('#2C3E50')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('white')
        ax.spines['bottom'].set_color('white')

        ax.text(0.5, 0.95, f'Week: {week_date}', transform=ax.transAxes,
                ha='center', va='top', fontsize=12, color='#BDC3C7')

        if max(stats) > 0:
            best_day_index = stats.index(max(stats))
            bars[best_day_index].set_color('#FFD700')
            bars[best_day_index].set_alpha(1.0)

        plt.tight_layout()
        filename = f"weekly_poll_stats_{week_date.replace('/', '_')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight',
                    facecolor='#2C3E50', edgecolor='none')
        plt.close()

        print(f"Generated static poll statistics graph: {filename}")
        return filename

    except Exception as e:
        print(f"Error creating static poll graph: {e}")
        return None


def tweet_weekly_statistic(day_conversion, quote_string, statistic, date_of_week, psql_database):
    tilda_quote_index = quote_string.index('~')
    question_tweet_index = quote_string.index(
        "What do you think about the quote - is it influential to you?")
    author_quote_string = quote_string[
                          tilda_quote_index + 1:question_tweet_index - 1]
    tweet_quote_string = quote_string[0:tilda_quote_index - 1]
    tweet_str = f"{day_conversion}'s quote, {tweet_quote_string} by {author_quote_string}, was found the most influential to about {statistic}% of the people that participated this week!" + '\n' + "#AspireToInspire"
    graph_filename = create_weekly_poll_graph(psql_database, date_of_week)
    if graph_filename:
        tweet_image_from_file(graph_filename, tweet_str)
        if os.path.exists(graph_filename):
            # os.remove(graph_filename)
            pass
    else:
        client = tweepy.Client(api_bearer_token, api_key, api_secret_key,
                               api_access_token, api_secret_access_token)
        client.create_tweet(text=tweet_str)
        print("Posted text-only weekly summary (graph generation failed)")


def tweet_image_from_file(filename, message):
    client = tweepy.Client(api_bearer_token, api_key, api_secret_key,
                           api_access_token, api_secret_access_token)
    tweeper = tweepy.API(authenticator)
    try:
        file_size = os.path.getsize(filename)
        print(f"File size: {file_size / (1024 * 1024):.2f} MB")

        if filename.lower().endswith('.gif'):
            max_size = 15 * 1024 * 1024
        else:
            max_size = 5 * 1024 * 1024

        if file_size > max_size:
            print(f"File too large: {file_size} bytes (max: {max_size} bytes)")
            return None

        print(f"Uploading media file: {filename}")
        media = tweeper.media_upload(filename)
        print(f"Uploaded media with ID: {media.media_id}")

        if len(message) > 280:
            print(f"Message too long: {len(message)} characters")
            message = message[:276] + "..."

        print(f"Creating tweet with message length: {len(message)}")
        sunday_tweet = client.create_tweet(text=message, media_ids=[media.media_id])

        file_extension = filename.lower().split('.')[-1]
        if file_extension == 'gif':
            print("Detected GIF format for follow-up tweet.")
            follow_up_text = "🎬 This animated visualization shows how engagement built up throughout the week! Keep engaging with our daily polls to help us understand what motivates you most! 💪✨"
            print("Follow-up text for GIF created.")
        else:
            follow_up_text = "📈 This week's data shows the power of inspirational quotes! Keep engaging with our daily polls to help us understand what motivates you most! 💪"
        print("Creating follow-up tweet...")
        client.create_tweet(
            text=follow_up_text,
            in_reply_to_tweet_id=sunday_tweet.data['id'])
        print("Successfully posted weekly statistics graph with analysis!")
        return sunday_tweet.data['id']
    except Exception as e:
        print(f"Unexpected error posting image tweet: {e}")
        return None


def photo_for_sunday():
    current_time = datetime.now()
    time_after_week = current_time + timedelta(days=5)
    time_string = current_time.strftime(
        "%m/%d/%y") + "-" + time_after_week.strftime("%m/%d/%y")
    return time_string


def retrieve_week_dates(psql_database):
    week_dates_list = []
    cursor = psql_database.cursor()
    cursor.execute("SELECT week FROM poll_distribution")
    weeks = cursor.fetchall()
    for datapoint in weeks:
        if len(datapoint) > 0:
            week_dates_list.append(datapoint[0])
    return week_dates_list


def find_current_date(psql_database):
    # Calculate the Monday-Saturday week interval that contains today's date
    current_time = datetime.now()
    current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday

    # Find the Monday of this week
    days_since_monday = current_weekday
    monday_of_this_week = current_time - timedelta(days=days_since_monday)

    # Calculate Saturday of this week (5 days after Monday)
    saturday_of_this_week = monday_of_this_week + timedelta(days=5)

    # Format as MM/dd/yy-MM/dd/yy
    current_week_string = monday_of_this_week.strftime("%m/%d/%y") + "-" + saturday_of_this_week.strftime("%m/%d/%y")

    print(f"Calculated current week: {current_week_string}")

    # Check if this week exists in the database
    cursor = psql_database.cursor()
    cursor.execute("SELECT week FROM poll_distribution WHERE week = %s", (current_week_string,))
    existing_week = cursor.fetchone()

    if existing_week:
        print(f"Found existing week in database: {current_week_string}")
        return current_week_string
    else:
        # If current calculated week doesn't exist, get the most recent week from database
        week_list = retrieve_week_dates(psql_database)
        if week_list:
            print("Week list:", week_list)
            most_recent = week_list[len(week_list) - 1]
            print(f"Using most recent week from database: {most_recent}")
            return most_recent
        else:
            # If no weeks exist, return the calculated current week
            print(f"No weeks in database, using calculated week: {current_week_string}")
            return current_week_string


def date_creation():
    current_time = datetime.now()
    time_after_week = current_time + timedelta(days=5)
    time_string = current_time.strftime(
        "%m/%d/%y") + "-" + time_after_week.strftime("%m/%d/%y")
    return time_string


def motivation_ftd():
    global today_weekday
    run_internet_check()
    db_connection = create_db_connection(
        user_name="postgres.xprikamuiprhvovypaoi",
        user_password=DB_PASSWORD,
        db_name="postgres",
        host="aws-1-us-west-1.pooler.supabase.com",
        port=6543,
        # sslmode=DB_SSLMODE
    )
    db_connection.set_session(autocommit=True)
    weekday_index = datetime.now().strftime("%A")
    today_weekday = [x for x, y in day_index.items() if weekday_index == y][0]
    # today_weekday = 1
    print("Today is:", weekday_index, "(index:", today_weekday, ")")
    print("YDAY:", f"{(date.today() - timedelta(days=1)).isoformat()}T00:00:00Z")

    if today_weekday == 0:
        week_date = date_creation()
        try:
            execute_query(db_connection,
                          "CREATE TABLE IF NOT EXISTS poll_distribution (week TEXT NULL, Monday DECIMAL(5,2) NULL, Tuesday DECIMAL(5,2) NULL, Wednesday DECIMAL(5,2) NULL, Thursday DECIMAL(5,2) NULL, Friday DECIMAL(5,2) NULL, Saturday DECIMAL(5,2) NULL, PRIMARY KEY (week))")
            execute_query(db_connection,
                          "CREATE TABLE IF NOT EXISTS tweet_distribution (week TEXT NULL, Monday TEXT NULL, Tuesday TEXT NULL, Wednesday TEXT NULL, Thursday TEXT NULL, Friday TEXT NULL, Saturday TEXT NULL, PRIMARY KEY (week))")
            execute_query(db_connection,
                          f"INSERT INTO poll_distribution (week) VALUES ('{week_date}')")
            execute_query(db_connection,
                          f"INSERT INTO tweet_distribution (week) VALUES ('{week_date}')")
            tweet_poll()
        except:
            print("!!!")
            tweet_poll()
    elif today_weekday < 6:
        date_of_week = find_current_date(db_connection)
        print("Current date of week:", date_of_week)
        prior_day_stats, prior_tweet = get_recent_tweet_data()
        print("Prior day stats:", prior_day_stats, prior_tweet)
        store_poll_statistics(db_connection, prior_day_stats,
                              date_of_week)
        store_tweet_info(db_connection, prior_tweet, date_of_week)
        tweet_poll()
    else:
        date_of_week = find_current_date(db_connection)
        prior_day_stats, prior_tweet = get_recent_tweet_data()
        store_poll_statistics(db_connection, prior_day_stats,
                              date_of_week)
        store_tweet_info(db_connection, prior_tweet, date_of_week)
        week_stat = find_best_poll_statistics(db_connection)
        stat_index = find_best_stat_index(db_connection, week_stat)
        index_quote = retrieve_most_influential_quote(db_connection,
                                                      stat_index,
                                                      date_of_week)
        tweet_weekly_statistic(stat_index, index_quote, week_stat, date_of_week, db_connection)


motivation_ftd()

"""
def format_quotes_file():
  index = 0
  with open("Twitter_Bot_Setup/quotes.txt", "r") as quotes_file:
      lines = quotes_file.read().splitlines()
      print(lines.index('~Anonymous'))
      if line[0] != "\"":
          with open("Twitter_Bot_Setup/quotes.txt", "w") as write_quotes_file:
              write_quotes_file.seek(index)
              tilda_substring = (line.index("~") - 1)
              print("\"" + line[:tilda_substring] + "\"" + line[tilda_substring:])
  pass
"""