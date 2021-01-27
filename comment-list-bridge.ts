import { TweetObject } from "./tweet.ts";

export class CommentBridge {
    body: string;
    author: {name: string};
    score: number;

    constructor(comment: TweetObject) {
        this.author = {name: comment.user.name};
        this.body = comment.text;
        this.score = 0;
    }
}
