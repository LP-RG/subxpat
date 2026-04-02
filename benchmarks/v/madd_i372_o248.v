module madd_i372_o248 (a, b, c, r);
input [123:0] a,b,c;
output [247:0] r;

assign r = (a * b) + c;

endmodule
