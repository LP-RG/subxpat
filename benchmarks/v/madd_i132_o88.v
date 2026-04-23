module madd_i132_o88 (a, b, c, r);
input [43:0] a,b,c;
output [87:0] r;

assign r = (a * b) + c;

endmodule
