export interface TweetObject {
    coordinates:               Coordinates | null;
    favorited:                 boolean;
    truncated:                 boolean;
    created_at:                string;
    id_str:                    string;
    entities:                  MentionTLResponseEntities;
    in_reply_to_user_id_str:   null | string;
    contributors:              null;
    text:                      string;
    retweet_count:             number;
    in_reply_to_status_id_str: null  | string;
    id:                        number;
    geo:                       Coordinates | null;
    retweeted:                 boolean;
    in_reply_to_user_id:       number | null;
    place:                     null;
    user:                      User;
    in_reply_to_screen_name:   null | string;
    source:                    string;
    in_reply_to_status_id:     null;
}

export interface Coordinates {
    coordinates: number[];
    type:        string;
}

export interface MentionTLResponseEntities {
    urls:          any[];
    hashtags:      Hashtag[];
    user_mentions: UserMention[];
}

export interface Hashtag {
    text:    string;
    indices: number[];
}

export interface UserMention {
    name:        string;
    id_str:      string;
    id:          number;
    indices:     number[];
    screen_name: string;
}

export interface User {
    profile_sidebar_fill_color:         string;
    profile_sidebar_border_color:       string;
    profile_background_tile:            boolean;
    name:                               string;
    profile_image_url:                  string;
    created_at:                         string;
    location:                           string;
    follow_request_sent:                boolean;
    profile_link_color:                 string;
    is_translator:                      boolean;
    id_str:                             string;
    entities:                           UserEntities;
    default_profile:                    boolean;
    contributors_enabled:               boolean;
    favourites_count:                   number;
    url:                                string;
    profile_image_url_https:            string;
    utc_offset:                         number;
    id:                                 number;
    profile_use_background_image:       boolean;
    listed_count:                       number;
    profile_text_color:                 string;
    lang:                               string;
    followers_count:                    number;
    protected:                          boolean;
    notifications:                      null;
    profile_background_image_url_https: string;
    profile_background_color:           string;
    verified:                           boolean;
    geo_enabled:                        boolean;
    time_zone:                          string;
    description:                        string;
    default_profile_image:              boolean;
    profile_background_image_url:       string;
    statuses_count:                     number;
    friends_count:                      number;
    following:                          null;
    show_all_inline_media:              boolean;
    screen_name:                        string;
}

export interface UserEntities {
    url:         Description;
    description: Description;
}

export interface Description {
    urls: URL[];
}

export interface URL {
    expanded_url: null;
    url:          string;
    indices:      number[];
}
