module madd_i39_o26 (a, b, c, r);
input [12:0] a,b,c;
output [25:0] r;

assign r = (a * b) + c;

endmodule
