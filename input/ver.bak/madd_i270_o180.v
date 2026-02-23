module madd_i270_o180 (a, b, c, r);
input [89:0] a,b,c;
output [179:0] r;

assign r = (a * b) + c;

endmodule
