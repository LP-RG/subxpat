module madd_i144_o96 (a, b, c, r);
input [47:0] a,b,c;
output [95:0] r;

assign r = (a * b) + c;

endmodule
