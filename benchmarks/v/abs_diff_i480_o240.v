module abs_diff_i480_o240(a,b,r);
input [239:0] a,b;
output [239:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
