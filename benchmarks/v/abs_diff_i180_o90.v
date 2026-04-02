module abs_diff_i180_o90(a,b,r);
input [89:0] a,b;
output [89:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
