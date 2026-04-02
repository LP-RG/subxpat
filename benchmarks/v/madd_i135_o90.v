module madd_i135_o90 (a, b, c, r);
input [44:0] a,b,c;
output [89:0] r;

assign r = (a * b) + c;

endmodule
