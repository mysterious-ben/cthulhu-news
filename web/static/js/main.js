const USER_ID = "user_id";
const ARTICLES = "articles";
const LIKE_BTN = "[data-like-btn]"; // data-like-btn="{{ article['id'] }}"
const LIKE_BTN_DATASET = "likeBtn"; // interpolation of data-like-btn attribute
const LIKES_URL = "/react";

let main = null;
document.addEventListener("DOMContentLoaded", () => main = new Main());

class Main {
    userId = null;
    likedArticles = [];
    httpUtils = null;

    constructor() {
        this.initStorage();
        this.updateLikeButtons();
        this.httpUtils = new HttpUtils(this.userId);
    }

    initStorage() {
        this.userId = localStorage.getItem(USER_ID);
        this.likedArticles = localStorage.getItem(ARTICLES)?.split(',') || [];

        if (this.userId === null) {
            this.userId = new Date().getTime() + '';
            console.log("New user id: " + this.userId);
            localStorage.setItem(USER_ID, this.userId);
        }
    }

    updateLikeButtons() {
        const buttons = document.querySelectorAll(LIKE_BTN);
        buttons.forEach(button => {
            const articleId = button.dataset[LIKE_BTN_DATASET];
            button.disabled = this.likedArticles.includes(articleId);
        });
    }

    setArticles(articleId) {
        this.likedArticles.push(articleId);
        localStorage.setItem(ARTICLES, this.likedArticles.join(','));
    }

    updateBtnValue (htmlElementId, html) {
        if (html) {
            document.getElementById(htmlElementId).outerHTML = html;
        }
    }

    likeClick = async (reaction, articleId, htmlElementId) => {
        if (this.likedArticles.includes(articleId)) return;

        this.setArticles(articleId);

        const html = await this.httpUtils.postLike(reaction, articleId);
        this.updateBtnValue(htmlElementId, html);

        this.updateLikeButtons();
    }
}

class HttpUtils {
    userId = null;
    constructor(userId) {
        this.userId = userId;
    }

    async postLike (reaction, articleId) {
        try {
            const response = await fetch(
                `${LIKES_URL}/${reaction}/${articleId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: this.userId
                    })
                }
            );

            return await response.text();
        } catch (e) {
            console.error(e);
        }
    }
}