"""CRM Integration for Educational Platform Support Assistant"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class CRMIntegration:
    """CRM integration to handle user data and support tickets"""
    
    def __init__(self, crm_path: str = "crm"):
        """Initialize CRM integration with path to CRM data"""
        self.crm_path = crm_path
        self.users_file = os.path.join(crm_path, "users.json")
        self.tickets_file = os.path.join(crm_path, "tickets.json")
        self.users = self._load_users()
        self.tickets = self._load_tickets()
    
    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            with open(self.users_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return {user["id"]: user for user in data.get("users", [])}
        return {}
    
    def _load_tickets(self) -> Dict:
        """Load tickets from JSON file"""
        if os.path.exists(self.tickets_file):
            with open(self.tickets_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return {ticket["id"]: ticket for ticket in data.get("tickets", [])}
        return {}
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user information by user ID"""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user information by email"""
        for user in self.users.values():
            if user.get("email") == email:
                return user
        return None
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Get ticket information by ticket ID"""
        return self.tickets.get(ticket_id)
    
    def get_user_tickets(self, user_id: str) -> List[Dict]:
        """Get all tickets for a specific user"""
        return [ticket for ticket in self.tickets.values() if ticket.get("user_id") == user_id]
    
    def create_ticket(self, user_id: str, subject: str, description: str, priority: str = "medium") -> str:
        """Create a new support ticket"""
        # Generate new ticket ID
        ticket_id = f"ticket_{len(self.tickets) + 1:03d}"
        
        # Create ticket data
        ticket = {
            "id": ticket_id,
            "user_id": user_id,
            "subject": subject,
            "description": description,
            "status": "open",
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "assigned_to": None
        }
        
        # Add to tickets dictionary
        self.tickets[ticket_id] = ticket
        
        # Save to file
        self._save_tickets()
        
        return ticket_id
    
    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update ticket status"""
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["status"] = status
            if status == "closed" and "resolved_at" not in self.tickets[ticket_id]:
                self.tickets[ticket_id]["resolved_at"] = datetime.now().isoformat()
            self._save_tickets()
            return True
        return False
    
    def assign_ticket(self, ticket_id: str, agent_id: str) -> bool:
        """Assign ticket to support agent"""
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["assigned_to"] = agent_id
            self._save_tickets()
            return True
        return False
    
    def _save_tickets(self) -> None:
        """Save tickets to JSON file"""
        # Convert tickets dict to list
        tickets_list = list(self.tickets.values())
        
        # Prepare data structure
        data = {"tickets": tickets_list}
        
        # Save to file
        with open(self.tickets_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    
    def get_ticket_context(self, ticket_id: str) -> str:
        """Get context information for a ticket including user details"""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return "Тикет не найден."
        
        user = self.get_user(ticket["user_id"])
        if not user:
            return f"Тикет: {ticket['subject']}\nОписание: {ticket['description']}"
        
        context = f"Пользователь: {user['name']} ({user['email']})\n"
        context += f"Тип подписки: {user['subscription_type']}\n"
        context += f"Тикет: {ticket['subject']}\n"
        context += f"Описание: {ticket['description']}\n"
        context += f"Статус: {ticket['status']}\n"
        context += f"Приоритет: {ticket['priority']}"
        
        return context


# Example usage
if __name__ == "__main__":
    crm = CRMIntegration()
    ticket = crm.get_ticket("ticket_001")
    print(ticket)
    context = crm.get_ticket_context("ticket_001")
    print(context)