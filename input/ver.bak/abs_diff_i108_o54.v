module abs_diff_i108_o54(a,b,r);
input [53:0] a,b;
output [53:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
