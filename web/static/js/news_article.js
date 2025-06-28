// static/js/main.js

const USER_ID = "user_id";
const REACTED_ARTICLES = "reacted_articles";
const COMMENTED_ARTICLES = "commented_articles";
const REACT_BTN = "[data-react-btn]";
const REACT_BTN_DATASET = "reactBtn"; // interpolation of data-react-btn attribute
const COMMENT_FORM = "[data-comment-form]";
const COMMENT_FORM_DATASET = "commentForm"; // interpolation of data-react-btn attribute

let news_article = null;
document.addEventListener("DOMContentLoaded", () => news_article = new NewsArticle());

class NewsArticle {
    userId = null;
    reactedArticles = [];
    commentedArticles = [];

    constructor() {
        this.initStorage();
        this.updateReactionButtons();
        this.updateCommentForms();
    }

    initStorage() {
        this.userId = localStorage.getItem(USER_ID);
        this.reactedArticles = localStorage.getItem(REACTED_ARTICLES)?.split(',') || [];
        this.commentedArticles = localStorage.getItem(COMMENTED_ARTICLES)?.split(',') || [];

        if (this.userId === null) {
            this.userId = new Date().getTime() + '';
            console.log("New user id: " + this.userId);
            localStorage.setItem(USER_ID, this.userId);
        }
    }

    // --- Reactions ---

    updateReactionButtons() {
        const buttons = document.querySelectorAll(REACT_BTN);
        buttons.forEach(button => {
            const articleId = button.dataset[REACT_BTN_DATASET];
            button.disabled = this.reactedArticles.includes(articleId);
        });
    }

    setReactedArticles(articleId) {
        this.reactedArticles.push(articleId);
        localStorage.setItem(REACTED_ARTICLES, this.reactedArticles.join(','));
    }

    reactionClick = async (articleId) => {
        if (this.reactedArticles.includes(articleId)) return;

        this.setReactedArticles(articleId);
        this.updateReactionButtons();
    }

    // --- Comments ---

    updateCommentForms() {
        const forms = document.querySelectorAll(COMMENT_FORM);
        forms.forEach(form => {
            const articleId = form.dataset[COMMENT_FORM_DATASET];
            if (this.commentedArticles.includes(articleId)) {
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton) submitButton.disabled = true;
                const thankElement = document.getElementById(`thanks-message-${articleId}`);
                if (thankElement) thankElement.style.display = 'block';
                form.style.display = 'none';
            }
        });
    }

    setCommentedArticles(articleId) {
        this.commentedArticles.push(articleId);
        localStorage.setItem(COMMENTED_ARTICLES, this.commentedArticles.join(','));
    }

    commentSubmit = async (articleId) => {
        if (this.commentedArticles.includes(articleId)) return false;

        this.setCommentedArticles(articleId);
        return true;
    }
}
