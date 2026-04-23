module madd_i720_o480 (a, b, c, r);
input [239:0] a,b,c;
output [479:0] r;

assign r = (a * b) + c;

endmodule
