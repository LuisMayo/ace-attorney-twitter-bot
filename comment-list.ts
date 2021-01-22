export interface CommentList {
    data:     Data;
    includes: Includes;
}

export interface Data {
    referenced_tweets: ReferencedTweet[];
    text:              string;
    author_id:         string;
    id:                string;
}

export interface ReferencedTweet {
    type: string;
    id:   string;
}

export interface Includes {
    users: User[];
}

export interface User {
    id:       string;
    name:     string;
    username: string;
}
