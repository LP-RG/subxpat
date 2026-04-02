module madd_i189_o126 (a, b, c, r);
input [62:0] a,b,c;
output [125:0] r;

assign r = (a * b) + c;

endmodule
