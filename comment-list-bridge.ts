import { CommentList } from "./comment-list.ts";

export class CommentBridge {
    body: string;
    author: {name: string};

    constructor(comment: CommentList) {
        this.author = {name: comment.includes.users[0].name};
        this.body = comment.data.text;
    }
}
